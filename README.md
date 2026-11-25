# SportRent - ćwiczenie z CSRF (materiał dla prowadzącego)

To repozytorium łączy aplikację `sport-rent-backend` (FastAPI, PostgreSQL) i
`sport-rent-frontend` (React, Vite). Służy do lokalnego pokazania ataku CSRF na
zmianę adresu e-mail konta oraz do przećwiczenia poprawki. Kod zawiera celowy,
domyślnie wyłączony przełącznik `CSRF_DEMO_ENABLED`. Używaj wyłącznie osobnej
bazy i kont testowych.

## Cel zajęć

Student powinien umieć:

1. Wskazać operację zmieniającą stan: `POST /auth/account/email`.
2. Wyjaśnić, dlaczego przeglądarka ofiary dołącza cookie sesyjne do formularza
   wysłanego z innego originu.
3. Rozróżnić origin od site i wyjaśnić, czemu `SameSite=Lax` oraz CORS nie
   zatrzymują tej lokalnej demonstracji.
4. Porównać zachowanie endpointu z kontrolą `require_csrf(request)` i bez niej.
5. Sprawdzić poprawkę testem oraz w przeglądarce.

## Układ repozytorium

| Ścieżka | Rola |
| --- | --- |
| `sport-rent-backend/app/api/routes/account_email.py` | Endpoint zmiany e-maila i celowy warunek pomijający CSRF. |
| `sport-rent-backend/app/api/auth_helpers.py` | Wystawianie cookies i funkcja `require_csrf()`. |
| `sport-rent-backend/docs/csrf-demo/attack.html` | Strona atakującego z automatycznie wysyłanym formularzem. |
| `sport-rent-backend/docs/csrf-demo/README.md` | Szczegóły lokalnej demonstracji. |
| `sport-rent-backend/tests/integration/test_csrf_demo.py` | Test trybu chronionego i demonstracyjnego. |
| `sport-rent-frontend/src/api/user.ts` | Prawidłowe żądanie profilu z nagłówkiem `X-CSRF-Token`. |
| `sport-rent-frontend/src/features/product/ProductComments.tsx` | Komentarz z linkiem do strony atakującego. |

## Wymagania i przygotowanie

- Python 3.14+, `uv`, Node.js 22+, `pnpm` i Docker z działającym silnikiem.
- Wolne porty `5432`, `8000`, `5173` i `9000`.
- Trzy lub cztery terminale. Wszystkie adresy w przeglądarce muszą używać
  **`127.0.0.1`**, nie zamiennie `localhost`.

W katalogu `sport-rent-backend`:

```powershell
Copy-Item .env.example .env
```

W pliku `.env` ustaw dwa **różne** losowe sekrety
`JWT_ACCESS_SECRET` i `JWT_REFRESH_SECRET` (każdy co najmniej 32 znaki), a także:

```dotenv
CSRF_DEMO_ENABLED=true
AUTH_COOKIE_SECURE=false
FRONTEND_URL=http://127.0.0.1:5173
```

`AUTH_COOKIE_SECURE=false` jest tu potrzebne tylko dla lokalnego HTTP. Plik
`.env` jest ignorowany przez Git; nie dodawaj go do commita.

W katalogu `sport-rent-frontend`:

```powershell
Copy-Item .env.example .env
pnpm install --frozen-lockfile
```

Domyślne `VITE_API_URL=http://127.0.0.1:8000` jest właściwe dla tego pokazu.

## Uruchomienie pokazu

1. W katalogu `sport-rent-backend` uruchom bazę, migracje i dane demonstracyjne:

   ```powershell
   docker compose up -d db
   uv sync --frozen
   uv run --env-file .env alembic upgrade head
   uv run --env-file .env python -m scripts.seed
   ```

   Jeśli produkty są już w bazie, komentarz-przynętę można dodać osobno przez
   `uv run --env-file .env python -m scripts.seed_csrf_demo_comment`.

2. W tym samym katalogu uruchom API:

   ```powershell
   uv run --env-file .env uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

3. W katalogu `sport-rent-frontend` uruchom interfejs:

   ```powershell
   pnpm dev
   ```

4. W katalogu `sport-rent-backend/docs/csrf-demo` uruchom stronę atakującego:

   ```powershell
   python -m http.server 9000 --bind 127.0.0.1
   ```

Sprawdź, czy odpowiadają `http://127.0.0.1:8000/health`,
`http://127.0.0.1:5173` i `http://127.0.0.1:9000/attack.html`.

## Przebieg demonstracji

1. Zaloguj konto testowe `jan.kowalski@poczta.pl`. Hasło jest wartością
   `SEED_USER_PASSWORD` z backendowego `.env`; domyślna wartość przykładu to
   `Test123!`. Zanotuj aktualny e-mail w `/rent/profile`.
2. Otwórz `http://127.0.0.1:5173/rent/product/rower-szosowy`. W komentarzu
   Mareczka znajduje się rzekomy kod `MAREK20` i link do strony na porcie 9000.
3. Kliknij link. Ukryty formularz wyśle `POST /auth/account/email` z polem
   `email=attacker@example.com`.
4. Wróć do profilu i odśwież stronę. Przy `CSRF_DEMO_ENABLED=true` e-mail
   zalogowanego konta zmieni się na `attacker@example.com` (HTTP 204).

To przeglądarka ofiary wysyła pasujące cookie `refresh_token`. Atakujący nie
poznaje jego wartości. Porty 9000 i 8000 są różnymi originami, ale przy tym
samym schemacie i hoście `127.0.0.1` należą do tego samego site. Formularz nie
potrafi dodać nagłówka `X-CSRF-Token`; dlatego poprawna kontrola serwera go
odrzuca. CORS ogranicza odczyt odpowiedzi przez obcą stronę, lecz nie blokuje
samego prostego żądania formularza.

## Zadanie dla studentów i rozwiązanie

Poproś studentów o znalezienie warunku w
`sport-rent-backend/app/api/routes/account_email.py`, który pomija sprawdzenie
CSRF w trybie demo. Minimalna poprawka polega na **bezwarunkowym** wywołaniu
`require_csrf(request)` przed zmianą e-maila. Po zmianie kodu uruchom API
ponownie. Przy pozostawieniu `CSRF_DEMO_ENABLED=true` komentarz-przynęta nadal
jest widoczny, ale atak powinien zakończyć się HTTP 403 i e-mail nie powinien
się zmienić. Zwykły formularz profilu nadal działa, ponieważ frontend dodaje
`X-CSRF-Token`.

Test automatyczny w katalogu backendu:

```powershell
uv run --env-file .env pytest tests/integration/test_csrf_demo.py -q
```

Obecny test sprawdza także celowo podatny tryb demo, więc po trwałym usunięciu
obejścia trzeba zaktualizować jego oczekiwania. Test korzysta z klienta HTTP,
a nie z prawdziwej przeglądarki; końcowy pokaz wykonaj też ręcznie.

Wersja do wdrożenia wymaga usunięcia przełącznika demonstracyjnego, ścisłej
listy dozwolonych originów, HTTPS i `Secure` dla cookie sesyjnego. Obecny
mechanizm porównania cookie z nagłówkiem to prosty double-submit; w aplikacji
publicznej warto użyć tokenu powiązanego z sesją lub podpisanego tokenu.

## Przywrócenie stanu między grupami

Po udanym ataku zmień e-mail konta z `attacker@example.com` na pierwotny adres
przez formularz profilu. Jeśli sesja wygasła, zaloguj się adresem
`attacker@example.com` i tym samym hasłem, a następnie przywróć e-mail.
Ponowny atak na konto, które już ma ten adres, nie pokaże widocznej zmiany;
atak na inne konto z zajętym adresem zwróci 409.

Po zajęciach ustaw `CSRF_DEMO_ENABLED=false` i uruchom backend ponownie.
Wyłączenie serwerów: przerwij trzy procesy aplikacji, a w katalogu backendu
wykonaj `docker compose down`. Nie używaj `down -v`, jeśli chcesz zachować
lokalne dane PostgreSQL.
