# -*- coding: utf-8 -*-
"""Schema cleanup: drop unused tables/cols + harden soft FKs.

Revision ID: 042
Revises: 041

- Drop case_tasks, case_comments, cabinet_plaidoirie_templates (product removed)
- Drop agenda_events.reminder_48h_sent_at (duplicate of reminder_2d)
- Add missing FKs for integrity (assistant, referral, pack invoice, audit, etc.)
- Sync prepaid_ai_credits from pack lots
"""

from alembic import op


revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def _add_fk(name: str, table: str, cols: str, ref_table: str, ref_cols: str, ondelete: str) -> None:
    op.execute(
        f"""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
            ALTER TABLE {table}
              ADD CONSTRAINT {name}
              FOREIGN KEY ({cols}) REFERENCES {ref_table}({ref_cols})
              ON DELETE {ondelete};
          END IF;
        END $$;
        """
    )


def _create_index_if_missing(name: str, table: str, cols: str) -> None:
    op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})")


def upgrade() -> None:
    # —— Legacy reminder alias → keep J-2 only ——
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'agenda_events'
              AND column_name = 'reminder_48h_sent_at'
          ) THEN
            UPDATE agenda_events
            SET reminder_2d_sent_at = reminder_48h_sent_at
            WHERE reminder_2d_sent_at IS NULL
              AND reminder_48h_sent_at IS NOT NULL;
            ALTER TABLE agenda_events DROP COLUMN reminder_48h_sent_at;
          END IF;
        END $$;
        """
    )

    # —— Product surfaces removed (empty on prod) ——
    op.execute("DROP TABLE IF EXISTS case_comments CASCADE")
    op.execute("DROP TABLE IF EXISTS case_tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS cabinet_plaidoirie_templates CASCADE")

    # —— Orphan cleanup before FK constraints ——
    op.execute(
        """
        UPDATE cases SET assistant_id = NULL
        WHERE assistant_id IS NOT NULL
          AND assistant_id NOT IN (SELECT id FROM users)
        """
    )
    op.execute(
        """
        UPDATE cabinets SET referred_by_cabinet_id = NULL
        WHERE referred_by_cabinet_id IS NOT NULL
          AND referred_by_cabinet_id NOT IN (SELECT id FROM cabinets)
        """
    )
    op.execute(
        """
        UPDATE plaidoirie_drafts SET validated_by = NULL
        WHERE validated_by IS NOT NULL
          AND validated_by NOT IN (SELECT id FROM users)
        """
    )
    op.execute(
        """
        UPDATE billing_credit_pack_purchases SET invoice_id = NULL
        WHERE invoice_id IS NOT NULL
          AND invoice_id NOT IN (SELECT id FROM billing_invoices)
        """
    )
    op.execute(
        """
        UPDATE billing_credit_pack_purchases SET created_by = NULL
        WHERE created_by IS NOT NULL
          AND created_by NOT IN (SELECT id FROM users)
        """
    )
    op.execute(
        """
        UPDATE audit_logs SET user_id = NULL
        WHERE user_id IS NOT NULL
          AND user_id NOT IN (SELECT id FROM users)
        """
    )
    op.execute(
        """
        UPDATE audit_logs SET cabinet_id = NULL
        WHERE cabinet_id IS NOT NULL
          AND cabinet_id NOT IN (SELECT id FROM cabinets)
        """
    )
    op.execute(
        """
        DELETE FROM cabinet_referrals
        WHERE referrer_cabinet_id NOT IN (SELECT id FROM cabinets)
           OR referee_cabinet_id NOT IN (SELECT id FROM cabinets)
        """
    )
    op.execute(
        """
        DELETE FROM plaidoirie_revisions
        WHERE cabinet_id NOT IN (SELECT id FROM cabinets)
           OR user_id NOT IN (SELECT id FROM users)
        """
    )
    op.execute(
        """
        DELETE FROM payment_transfer_requests
        WHERE cabinet_id NOT IN (SELECT id FROM cabinets)
           OR user_id NOT IN (SELECT id FROM users)
        """
    )
    op.execute(
        """
        UPDATE subscription_events SET created_by = NULL
        WHERE created_by IS NOT NULL
          AND created_by NOT IN (SELECT id FROM users)
        """
    )

    # Sync denormalized pack balance from truth table
    op.execute(
        """
        UPDATE cabinet_subscriptions cs
        SET prepaid_ai_credits = COALESCE((
            SELECT SUM(p.credits_remaining)::int
            FROM billing_credit_pack_purchases p
            WHERE p.cabinet_id = cs.cabinet_id
              AND p.status = 'paid'
              AND p.credits_remaining > 0
              AND (p.expires_at IS NULL OR p.expires_at >= NOW())
        ), 0)
        """
    )

    # —— Foreign keys ——
    _add_fk(
        "fk_cases_assistant_id_users",
        "cases",
        "assistant_id",
        "users",
        "id",
        "SET NULL",
    )
    _add_fk(
        "fk_cabinets_referred_by_cabinet_id",
        "cabinets",
        "referred_by_cabinet_id",
        "cabinets",
        "id",
        "SET NULL",
    )
    _add_fk(
        "fk_plaidoirie_drafts_validated_by",
        "plaidoirie_drafts",
        "validated_by",
        "users",
        "id",
        "SET NULL",
    )
    _add_fk(
        "fk_pack_purchases_invoice_id",
        "billing_credit_pack_purchases",
        "invoice_id",
        "billing_invoices",
        "id",
        "SET NULL",
    )
    _add_fk(
        "fk_pack_purchases_created_by",
        "billing_credit_pack_purchases",
        "created_by",
        "users",
        "id",
        "SET NULL",
    )
    _add_fk(
        "fk_audit_logs_user_id",
        "audit_logs",
        "user_id",
        "users",
        "id",
        "SET NULL",
    )
    _add_fk(
        "fk_audit_logs_cabinet_id",
        "audit_logs",
        "cabinet_id",
        "cabinets",
        "id",
        "SET NULL",
    )
    _add_fk(
        "fk_cabinet_referrals_referrer",
        "cabinet_referrals",
        "referrer_cabinet_id",
        "cabinets",
        "id",
        "CASCADE",
    )
    _add_fk(
        "fk_cabinet_referrals_referee",
        "cabinet_referrals",
        "referee_cabinet_id",
        "cabinets",
        "id",
        "CASCADE",
    )
    _add_fk(
        "fk_plaidoirie_revisions_cabinet_id",
        "plaidoirie_revisions",
        "cabinet_id",
        "cabinets",
        "id",
        "CASCADE",
    )
    _add_fk(
        "fk_plaidoirie_revisions_user_id",
        "plaidoirie_revisions",
        "user_id",
        "users",
        "id",
        "CASCADE",
    )
    _add_fk(
        "fk_payment_transfer_cabinet_id",
        "payment_transfer_requests",
        "cabinet_id",
        "cabinets",
        "id",
        "CASCADE",
    )
    _add_fk(
        "fk_payment_transfer_user_id",
        "payment_transfer_requests",
        "user_id",
        "users",
        "id",
        "CASCADE",
    )
    _add_fk(
        "fk_subscription_events_created_by",
        "subscription_events",
        "created_by",
        "users",
        "id",
        "SET NULL",
    )

    _create_index_if_missing("ix_cases_assistant_id", "cases", "assistant_id")
    _create_index_if_missing(
        "ix_cabinets_referred_by_cabinet_id", "cabinets", "referred_by_cabinet_id"
    )


def downgrade() -> None:
    # Soft downgrade: do not recreate removed product tables.
    for fk, table in (
        ("fk_subscription_events_created_by", "subscription_events"),
        ("fk_payment_transfer_user_id", "payment_transfer_requests"),
        ("fk_payment_transfer_cabinet_id", "payment_transfer_requests"),
        ("fk_plaidoirie_revisions_user_id", "plaidoirie_revisions"),
        ("fk_plaidoirie_revisions_cabinet_id", "plaidoirie_revisions"),
        ("fk_cabinet_referrals_referee", "cabinet_referrals"),
        ("fk_cabinet_referrals_referrer", "cabinet_referrals"),
        ("fk_audit_logs_cabinet_id", "audit_logs"),
        ("fk_audit_logs_user_id", "audit_logs"),
        ("fk_pack_purchases_created_by", "billing_credit_pack_purchases"),
        ("fk_pack_purchases_invoice_id", "billing_credit_pack_purchases"),
        ("fk_plaidoirie_drafts_validated_by", "plaidoirie_drafts"),
        ("fk_cabinets_referred_by_cabinet_id", "cabinets"),
        ("fk_cases_assistant_id_users", "cases"),
    ):
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {fk}")
