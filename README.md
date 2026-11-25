# SportRent — ćwiczenie z CSRF

To repozytorium zawiera backend (FastAPI, PostgreSQL) i frontend (React, Vite)
aplikacji do wypożyczania sprzętu sportowego. Przygotowany scenariusz pokazuje,
jak strona atakującego może zmienić e-mail zalogowanej osoby, jeśli serwer pominie
kontrolę CSRF. Można uruchomić atak lokalnie, poprawić kod i sprawdzić wynik.

Podatność jest włączana tylko przez `CSRF_DEMO_ENABLED=true`; domyślnie
przełącznik jest wyłączony. Do ćwiczenia używaj osobnej bazy i kont testowych.

## Od czego zacząć

- **Plik z podatnością do poprawy:**
  [`sport-rent-backend/app/api/routes/account_email.py`](sport-rent-backend/app/api/routes/account_email.py).
  W funkcji `change_email_from_cookie()` warunek `if not settings.csrf_demo_enabled`
  pomija sprawdzenie CSRF. To miejsce, które należy poprawić.
- **Kod sprawdzający token CSRF:**
  [`sport-rent-backend/app/api/auth_helpers.py`](sport-rent-backend/app/api/auth_helpers.py)
  — funkcja `require_csrf(request)`.
- **Strona atakującego:**
  [`sport-rent-backend/docs/csrf-demo/attack.html`](sport-rent-backend/docs/csrf-demo/attack.html).
  Po otwarciu wysyła ukryty formularz zmiany e-maila.

Pozostałe pliki, które pomogą prześledzić scenariusz:

| Plik | Do czego służy |
| --- | --- |
| [`sport-rent-frontend/src/api/authSession.ts`](sport-rent-frontend/src/api/authSession.ts) | Odczytuje cookie `csrf_token` i przygotowuje nagłówek `X-CSRF-Token`. |
| [`sport-rent-frontend/src/api/user.ts`](sport-rent-frontend/src/api/user.ts) | Wysyła poprawne żądanie zmiany e-maila z profilu. |
| [`sport-rent-backend/app/main.py`](sport-rent-backend/app/main.py) | Konfiguruje CORS dla API. |
| [`sport-rent-backend/tests/integration/test_csrf_demo.py`](sport-rent-backend/tests/integration/test_csrf_demo.py) | Testuje tryb chroniony i demonstracyjny. |
| [`sport-rent-backend/docs/csrf-demo/README.md`](sport-rent-backend/docs/csrf-demo/README.md) | Zawiera dodatkowy opis lokalnego pokazu. |

## Jak działa atak

1. Po zalogowaniu przeglądarka dostaje cookie sesyjne `refresh_token` oraz
   `csrf_token`.
2. Frontend odczytuje `csrf_token` i dodaje jego wartość do nagłówka
   `X-CSRF-Token` przy zmianie e-maila. Funkcja `require_csrf(request)` sprawdza,
   czy wartość z nagłówka zgadza się z cookie; w przeciwnym razie zwraca HTTP 403.
3. Strona atakującego wysyła zwykły formularz `POST /auth/account/email`.
   Przeglądarka dołącza cookie ofiary, ale formularz nie może ustawić własnego
   nagłówka `X-CSRF-Token`.
4. Przy `CSRF_DEMO_ENABLED=true` endpoint pomija kontrolę CSRF i zmienia e-mail.
   Po poprawce takie żądanie powinno zostać odrzucone.

**Gdzie w tym CORS?** Origin obejmuje protokół, host i port. Strony na
`127.0.0.1:9000` i `127.0.0.1:8000` mają różne originy, choć należą do tego
samego site. Dlatego `SameSite=Lax` nie zatrzymuje żądania w tym przykładzie.
CORS (*Cross-Origin Resource Sharing*) to sposób, w jaki API informuje
przeglądarkę, którym originom pozwala korzystać z odpowiedzi i wykonywać
żądania wymagające wcześniejszej zgody. Zwykły formularz HTML może dotrzeć do
API mimo ograniczeń CORS. Gdyby JavaScript atakującego próbował wysłać nagłówek
`X-CSRF-Token`, przeglądarka najpierw wysłałaby zapytanie *preflight* i bez
zgody API nie wysłałaby właściwego `POST`. Konfiguracja API dopuszcza frontend
na porcie 5173, a nie stronę atakującego na porcie 9000.

Ten lokalny układ ma ograniczenie: cookie nie są oddzielone portami, więc
JavaScript strony na porcie 9000 mógłby odczytać cookie `csrf_token`. Dostarczony
`attack.html` tego nie robi; pokazuje atak przez zwykły formularz i skutek
pominięcia kontroli CSRF. Nie traktuj tego jako dowodu odporności na każdy kod
działający na tym samym hoście.

## Przygotowanie

- Python 3.14+, `uv`, Node.js 22+, `pnpm` i Docker z działającym silnikiem.
- Wolne porty `5432`, `8000`, `5173` i `9000`.
- Trzy lub cztery terminale. W całym ćwiczeniu używaj adresu **`127.0.0.1`**;
  nie mieszaj go z `localhost`.

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

`AUTH_COOKIE_SECURE=false` pozwala użyć cookie przez lokalne HTTP. Plik `.env`
jest ignorowany przez Git; nie dodawaj go do commita.

W katalogu `sport-rent-frontend`:

```powershell
Copy-Item .env.example .env
pnpm install --frozen-lockfile
```

Domyślne `VITE_API_URL=http://127.0.0.1:8000` pasuje do tego ćwiczenia.

## Uruchomienie

1. W katalogu `sport-rent-backend` uruchom bazę, migracje i dane demonstracyjne:

   ```powershell
   docker compose up -d db
   uv sync --frozen
   uv run --env-file .env alembic upgrade head
   uv run --env-file .env python -m scripts.seed
   ```

   Jeśli produkty są już w bazie, dodaj tylko komentarz z linkiem do strony
   atakującego: `uv run --env-file .env python -m scripts.seed_csrf_demo_comment`.

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

## Sprawdzenie ataku

1. Zaloguj się na konto testowe `jan.kowalski@poczta.pl`. Hasło określa
   `SEED_USER_PASSWORD` w backendowym `.env` (przykładowo `Test123!`). Zapisz
   aktualny e-mail widoczny w `/rent/profile`.
2. Otwórz `http://127.0.0.1:5173/rent/product/rower-szosowy`. W komentarzu
   Mareczka znajduje się rzekomy kod `MAREK20` i link do strony na porcie 9000.
3. Kliknij link. Strona na porcie 9000 wyśle formularz z adresem
   `attacker@example.com` do `POST /auth/account/email`.
4. Wróć do profilu i odśwież stronę. Przy `CSRF_DEMO_ENABLED=true` e-mail
   zalogowanego konta zmieni się na `attacker@example.com` (HTTP 204).

Przeglądarka wysyła w tym żądaniu cookie `refresh_token`; strona atakującego nie
odczytuje jego wartości. Efekt ataku widać po ponownym otwarciu profilu.

## Poprawka i weryfikacja

W `account_email.py` znajdź warunek, który pomija sprawdzenie CSRF w trybie demo.
Poprawka polega na **bezwarunkowym** wywołaniu `require_csrf(request)` przed
zmianą e-maila. Uruchom API ponownie i powtórz atak przy
`CSRF_DEMO_ENABLED=true`. Link w komentarzu nadal będzie widoczny, ale żądanie
powinno zakończyć się HTTP 403, a e-mail pozostać bez zmian. Zmiana e-maila z
profilu powinna nadal działać, ponieważ frontend dodaje `X-CSRF-Token`.

Przed poprawką możesz uruchomić test w katalogu backendu:

```powershell
uv run --env-file .env pytest tests/integration/test_csrf_demo.py -q
```

Test oczekuje również, że celowo podatny tryb demo przyjmie atak. Po poprawce
to oczekiwanie będzie nieaktualne i test trzeba dostosować: brak tokenu CSRF
powinien oznaczać HTTP 403 także w trybie demo. Test używa klienta HTTP, więc
sprawdź wynik także w przeglądarce.

Wersja do wdrożenia wymaga usunięcia przełącznika demonstracyjnego, ścisłej
listy dozwolonych originów, HTTPS i `Secure` dla cookie sesyjnego. Obecny
mechanizm porównania cookie z nagłówkiem to prosty double-submit; w aplikacji
publicznej warto użyć tokenu powiązanego z sesją lub podpisanego tokenu.

## Przywrócenie stanu

Po udanym ataku zmień e-mail konta z `attacker@example.com` na pierwotny adres
przez formularz profilu. Jeśli sesja wygasła, zaloguj się adresem
`attacker@example.com` i tym samym hasłem, a następnie przywróć e-mail.
Ponowny atak na konto, które już ma ten adres, nie pokaże widocznej zmiany;
atak na inne konto z zajętym adresem zwróci 409.

Po ćwiczeniu ustaw `CSRF_DEMO_ENABLED=false` i uruchom backend ponownie. Zatrzymaj
procesy aplikacji, a w katalogu backendu wykonaj `docker compose down`. Jeśli
chcesz zachować dane PostgreSQL, nie dodawaj opcji `-v`.
