# LexHub — Comptes, Mailhog & script de test micro

## Liens utiles (local Docker)

| Service | URL |
|---------|-----|
| Application | http://localhost:3000 |
| API (Swagger) | http://localhost:8001/docs |
| **Mailhog** (emails locaux) | **http://localhost:8025** |
| MinIO | http://localhost:9001 |

> Les emails (OTP inscription, magic link, invitations) n’arrivent **pas** dans Gmail en local.  
> Ouvre **Mailhog** → onglet messages.

---

## Comptes de test & mots de passe

| Email | Mot de passe | Rôle / espace |
|-------|--------------|---------------|
| `demo@lexhub.space` | `LexHub2026!` | Admin cabinet — accès complet |
| `avocat@lexhub.space` | `LexHub2026!` | Avocat — plaidoirie, dossiers, docs |
| `assistant@lexhub.space` | `LexHub2026!` | Assistant — lecture limitée |
| `admin@webvoice.ma` | `WebVoice2026!` | Admin plateforme → `/admin` |
| `test@cabinet-rabat.ma` | `Test2026!` | Admin d’un autre cabinet (multi-tenant) |

> Anciens e-mails `@sanad.ma` : migrés vers `@lexhub.space` (Vague A).

---

## Script arabe — test micro plaidoirie (lire à voix haute)

Lis **lentement et clairement**, en العربية الفصحى, pendant ~30–45 secondes :

```
بسم الله الرحمن الرحيم.
السيد الرئيس، السادة المستشارون المحترمون.

أتشرف بأن أتقدم أمام محكمتكم الموقرة بهذه المرافعة
لفائدة موكلتي السيدة فاطمة العلوي،
ضد المدعى عليه السيد كريم بناني،
في ملف النفقة والحضانة عدد 2024/120.

إن الوقائع ثابتة بموجب عقد الزواج المبرم بتاريخ
الخامس عشر من شهر يونيو سنة ألفين وعشرين،
وبموجب شهادة ميلاد الابن القاصر يوسف.

وبناء على قواعد مدونة الأسرة،
فإن واجب النفقة يقع على عاتق الأب،
كما أن مصلحة المحضون تقتضي استقرار حضانته
لدى والدته.

ولهذه الأسباب، ألتمس من محكمتكم الموقرة
الحكم على المدعى عليه بأداء نفقة شهرية قدرها
ألفا درهم، مع شمول الحكم بالنفاذ المعجل،
وتحميله الصائر.

والسلام عليكم ورحمة الله تعالى وبركاته.
```

### Comment tester
1. Login `demo@lexhub.space` / `LexHub2026!`
2. **مرافعة** → صفحة فارغة أو نموذج
3. Langue STT = arabe (forcé)
4. **ميكروفون** → lire le script → attendre l’apparition du texte (~12 s par segment) → **إيقاف**
5. Ou **ملف صوتي** : enregistrer ce texte en mp3/wav puis uploader

> Whisper n’écrit **pas** mot à mot en direct comme Chrome : le texte arrive par **segments ~12 secondes**.  
> Pour un aperçu plus “live”, utilise aussi le bouton **Chrome** (secours navigateur).

---

## Google Docs
Le bouton ouvre un document Google vide et **copie la plaidoirie dans le presse-papiers**.  
Colle avec `Ctrl+V` (Windows) dans Docs pour modifier.

---

*LexHub · tests locaux · ENSA / WebVoice*
