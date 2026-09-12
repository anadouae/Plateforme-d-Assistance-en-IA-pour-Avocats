"use client";

import { LexProductModal } from "@/components/billing/lex-product-modal";

type Kind = "activated" | "reset" | "invite";

const COPY: Record<
  Kind,
  { tag: string; title: string; points: string[]; primary: string }
> = {
  activated: {
    tag: "Compte prêt",
    title: "Votre compte LexHub est activé",
    points: [
      "Vous pouvez vous connecter avec votre email et le mot de passe choisi.",
      "Accès immédiat à l’espace de votre cabinet.",
    ],
    primary: "Se connecter",
  },
  reset: {
    tag: "Mot de passe",
    title: "Mot de passe réinitialisé",
    points: [
      "Votre nouveau mot de passe est enregistré.",
      "Connectez-vous pour accéder à votre espace.",
    ],
    primary: "Se connecter",
  },
  invite: {
    tag: "Invitation",
    title: "Invitation acceptée",
    points: [
      "Votre compte est prêt — connectez-vous pour rejoindre le cabinet.",
    ],
    primary: "Se connecter",
  },
};

const COPY_AR: Record<
  Kind,
  { tag: string; title: string; points: string[]; primary: string }
> = {
  activated: {
    tag: "الحساب جاهز",
    title: "تم تفعيل حسابك على LexHub",
    points: [
      "يمكنكم تسجيل الدخول بالبريد وكلمة المرور التي اخترتموها.",
      "الوصول فوري إلى مساحة مكتبكم.",
    ],
    primary: "تسجيل الدخول",
  },
  reset: {
    tag: "كلمة المرور",
    title: "تمت إعادة تعيين كلمة المرور",
    points: [
      "كلمة المرور الجديدة محفوظة.",
      "سجّلوا الدخول للوصول إلى مساحتكم.",
    ],
    primary: "تسجيل الدخول",
  },
  invite: {
    tag: "دعوة",
    title: "تم قبول الدعوة",
    points: ["حسابكم جاهز — سجّلوا الدخول للانضمام إلى المكتب."],
    primary: "تسجيل الدخول",
  },
};

export function AuthSuccessModal({
  open,
  kind,
  ar = false,
  onClose,
}: {
  open: boolean;
  kind: Kind;
  ar?: boolean;
  onClose: () => void;
}) {
  const c = ar ? COPY_AR[kind] : COPY[kind];
  return (
    <LexProductModal
      open={open}
      onClose={onClose}
      tag={c.tag}
      title={c.title}
      points={c.points}
      primaryLabel={c.primary}
      onPrimary={onClose}
      secondaryLabel={ar ? "إغلاق" : "Fermer"}
      onSecondary={onClose}
      closeLabel={ar ? "إغلاق" : "Fermer"}
      zIndexClass="z-[80]"
    />
  );
}
