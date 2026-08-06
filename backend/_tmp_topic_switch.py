from app.services.conversation import is_topic_switch, is_followup_question, resolve_with_history
from app.services.topic_filter import is_immobilier_query
from app.services.reforms_corpus import search_reforms

h = [
    {
        "question": "ما هي آخر التعديلات حول قانون الحيوانات الضالة 19.25 والعقوبات؟",
        "answer": "loi 19.25 animaux",
        "summary": "19.25 animaux errants",
    }
]
for q in [
    "immobilier",
    "la loi dimmobile r doenne moi la liste des lioi lié à ca",
    "donne moi la reponse en francais",
    "cest quoi la loi",
]:
    print("---", q)
    print("  immo", is_immobilier_query(q))
    print("  switch", is_topic_switch(q, h))
    print("  followup", is_followup_question(q, h))
    sq, _, f = resolve_with_history(q, h)
    print("  followup_flag", f)
    print("  search", sq[:120].replace("\n", " | "))

_, cites, _ = search_reforms(
    "droit immobilier Maroc lois baux 49-16 67-12",
    locale="fr",
    years_back=25,
)
print("reforms", [c.label for c in cites])
