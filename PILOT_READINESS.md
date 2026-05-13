# RiceMap24 step 9.39 – Pilot readiness

Denne pakken gjør ikke nye appfunksjoner. Den legger til en konkret pilot-sjekk i admin/health, slik at appen kan testes med få aktører før offentlig lansering.

## Det som må være grønt før pilot

- database, uploads og backups ligger utenfor kode-mappen
- uploads og backups er skrivbare
- demo-seeding er trygg for valgt miljø
- staging/base-URL er satt når appen ligger på web
- Stripe er enten testkonfigurert eller eksplisitt deaktivert
- e-post er enten i manual mode eller med konfigurert provider
- minst én aktør er publisert og synlig på Explore

## Viktig test

1. Opprett eller åpne en aktør.
2. Legg inn/rediger en rett.
3. Last opp et bilde.
4. Publiser aktøren.
5. Åpne Explore.
6. Restart/redeploy.
7. Kontroller at profil, rett og bilde fortsatt finnes.
