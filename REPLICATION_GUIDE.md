# Как воспроизвести этот GitHub Profile Repository

Это руководство описывает текущую реализацию профиля `Asmoorr/asmoorr`: почти адаптивный `README.md`, три цветовые темы, переключение темы через GitHub Issue Forms, автоматически обновляемый Breakout-график контрибьютов и карточку посещений. Инструкция рассчитана на создание такого же репозитория с нуля под другим GitHub-аккаунтом.

> [!IMPORTANT] 
> Актуально на август 2026 года. Перед копированием сторонних Actions проверьте их актуальные версии.

## Что получится

После настройки у вас будет:

- профильный репозиторий `<USERNAME>/<USERNAME>`;
- светлая и тёмная версии каждой карточки;
- темы `Graphite Alloy`, `Mint Circuit` и `Violet Dusk` (или любые другие);
- вертикальные кнопки тем прямо в README;
- смена глобальной темы через создание служебного issue;
- обновление Breakout-графика и снимка счётчика посещений каждые 12 часов;
- проверка опубликованных файлов перед коммитом смены темы.

## Предварительные требования

Вам понадобятся:

- личный GitHub-аккаунт;
- публичный репозиторий с именем, точно совпадающим с именем аккаунта;
- Git;
- Python 3.10 или новее локально — скрипт использует современный синтаксис типов и `zip(..., strict=True)`;
- включённые GitHub Issues и GitHub Actions;
- право администратора репозитория для создания секрета и удаления служебных issues.

GitHub показывает README на странице профиля только тогда, когда репозиторий публичный, называется как пользователь и содержит непустой `README.md` в корне. См. [Managing your profile README](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme).

## Архитектура

```text
README.md
  ├─ внешние динамические карточки по HTTPS
  ├─ <picture> с light/dark URL
  ├─ Breakout SVG из ветки pacman-output
  ├─ visits SVG из ветки pacman-output
  └─ SVG-кнопки тем из main → Issue Forms

.github/profile-theme.json              активная глобальная тема
.github/profile-themes/*.json           цвета всех тем
.github/profile-theme-control-*.svg     кнопки тем, light/dark
.github/ISSUE_TEMPLATE/theme-*.yml      формы запроса смены темы
scripts/profile_theme.py                применение, генерация и проверки
```

Главный workflow объединяет две задачи, которые должны оставаться согласованными:

1. обновляет тему README и управляющих кнопок;
2. генерирует статические SVG в отдельную output-ветку.

Так README не разрастается генерируемыми артефактами, а `raw.githubusercontent.com` может отдавать SVG напрямую.

### Поток смены темы

```text
Клик по SVG-кнопке
  → открытие Issue Form с фиксированным title
  → событие issues: opened
  → resolve: название темы → theme id
  → apply: изменение README, state и SVG-кнопок
  → генерация и публикация всех Breakout/visits вариантов
  → проверка опубликованных SVG через GitHub API
  → коммит изменений темы в main
  → удаление служебного issue через PROFILE_ADMIN_TOKEN
```

Публикация артефактов идёт **до** коммита README. Поэтому новый README не должен указывать на ещё не существующие тематические SVG.

## Шаг 1. Создайте профильный репозиторий

На GitHub создайте публичный репозиторий `<USERNAME>/<USERNAME>` с включённым README. Затем клонируйте его:

```bash
git clone https://github.com/<USERNAME>/<USERNAME>.git
cd <USERNAME>
```

Во всех скопированных файлах замените:

- `Asmoorr` и `asmoorr` на ваше имя пользователя;
- имя, описание и `alt`-тексты в `README.md`;
- `utcOffset=3` на ваш UTC offset;
- ссылки на ваш аккаунт и репозиторий.

Регистр в URL GitHub обычно не мешает, но единообразное написание упрощает поиск ошибок.

## Шаг 2. Создайте структуру файлов

Минимальная структура для текущей системы:

```text
.
├── README.md
├── scripts/
│   └── profile_theme.py
└── .github/
    ├── profile-theme.json
    ├── profile-themes/
    │   ├── graphite.json
    │   ├── mint.json
    │   └── violet.json
    ├── ISSUE_TEMPLATE/
    │   ├── theme-graphite.yml
    │   ├── theme-mint.yml
    │   └── theme-violet.yml
    └── workflows/
        └── change-profile-theme.yml
```

Файлы `profile-theme-control-*.svg` создаёт команда `apply`; их не нужно рисовать вручную, но после генерации их нужно добавить в Git.

Скопируйте из этого репозитория актуальные версии:

- `scripts/profile_theme.py`;
- `.github/profile-themes/*.json`;
- `.github/profile-theme.json`;
- `.github/ISSUE_TEMPLATE/theme-*.yml`;
- `.github/workflows/change-profile-theme.yml`;
- структуру виджетов из `README.md`.

## Шаг 3. Настройте палитры

Каждый `.github/profile-themes/<id>.json` имеет такую схему:

```json
{
  "id": "mint",
  "name": "Mint Circuit",
  "colors": {
    "light": {
      "canvas": "FFFFFF",
      "surface": "F6F8FA",
      "border": "D1D9E0",
      "text": "1F2328",
      "text_muted": "59636E",
      "accent": "087F6D",
      "accent_emphasis": "066B5D",
      "accent_muted": "C8E9E2",
      "accent_surface": "EAF7F4",
      "on_accent": "FFFFFF",
      "chart": "169D87",
      "chart_muted": "8FD6C7",
      "breakout": ["EFF8F6", "C9EAE3", "8FD6C7", "45B7A1", "087F6D"]
    },
    "dark": {
      "...": "те же обязательные ключи"
    }
  }
}
```

Правила схемы проверяются `load_theme()`:

- имя файла равно `<id>.json`;
- `id` состоит только из строчных букв, цифр и дефисов;
- `id` внутри JSON совпадает с именем файла;
- присутствуют палитры `light` и `dark`;
- в каждой палитре есть все 13 токенов;
- `breakout` содержит ровно пять цветов;
- цвета записаны без `#`, потому что скрипт добавляет его при генерации SVG.

Токены используются так:

| Токен | Назначение |
|---|---|
| `canvas` | общий фон; сейчас зарезервирован для расширения |
| `surface` | фон карточек и кнопок |
| `border` | рамка карточек |
| `text`, `text_muted` | основной и вторичный текст |
| `accent`, `accent_emphasis` | главный и усиленный акцент |
| `accent_muted`, `accent_surface` | приглушённый акцент и фон выбранной кнопки |
| `on_accent` | текст на акцентном фоне |
| `chart`, `chart_muted` | графики и декоративные линии |
| `breakout` | пять уровней интенсивности contribution graph |

Активную тему укажите в `.github/profile-theme.json`:

```json
{
  "active": "violet"
}
```

## Шаг 4. Подготовьте README

В первой строке нужен ровно один маркер:

```markdown
<!-- profile-theme: violet -->
```

`profile_theme.py apply` останавливается, если маркер отсутствует или встречается более одного раза.

### Светлая и тёмная версии

Для каждого тематизируемого изображения используйте `<picture>`:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="DARK_URL">
  <img src="LIGHT_URL" alt="Описание изображения" />
</picture>
```

GitHub выбирает `<source>` по настройке цветовой схемы посетителя. `<img>` служит светлым вариантом и обязательным fallback. Для Breakout в текущем README также есть явный light-source:

```html
<picture data-importer="breakout">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/<OWNER>/<REPO>/pacman-output/breakout-contribution-graph-violet-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/<OWNER>/<REPO>/pacman-output/breakout-contribution-graph-violet.svg">
  <img alt="Breakout contribution graph" src="https://raw.githubusercontent.com/<OWNER>/<REPO>/pacman-output/breakout-contribution-graph-violet.svg">
</picture>
```

Скрипт определяет режим **построчно**: строка с `prefers-color-scheme: dark` получает dark-палитру, остальные URL — light-палитру. Не помещайте light- и dark-URL на одну строку и не переносите URL на несколько строк.

### Поддерживаемые внешние карточки

`update_widget_url()` знает следующие сервисы:

| Сервис | Что изменяет скрипт |
|---|---|
| `readme-typing-svg.demolab.com` | `color`; удаляет `background` |
| `github-profile-summary-cards.vercel.app` | фон, заголовок, текст, рамку, иконку и график |
| `github-readme-streak-stats-eight.vercel.app` | фон, рамку, stroke, ring, fire и все цвета текста |
| `komarev.com/ghpvc` | цвет, цвет логотипа и стиль |
| `capsule-render.vercel.app` | `color` |

Скрипт добавляет отсутствующий query parameter или заменяет существующий. Остальные параметры — размеры, имя пользователя, текст и длительность анимации — сохраняются.

### Ограничения GitHub Markdown и обходы

GitHub README не является обычной веб-страницей:

- нельзя выполнять собственный JavaScript;
- нельзя подключить произвольный CSS и менять CSS-переменные всей страницы;
- HTML санитизируется, поэтому интерактивные формы, скрипты и многие атрибуты недоступны;
- Markdown не умеет менять несколько файлов в репозитории по клику;
- нельзя перекрасить удалённый SVG CSS-стилями README;
- относительная ссылка не подходит для файла из другой ветки;
- содержимое внешних карточек зависит от доступности сторонних сервисов.

В реализации применены следующие обходы:

- `<picture>` и `prefers-color-scheme` вместо JavaScript для dark/light;
- заранее окрашенные SVG вместо CSS-фильтров;
- изображение внутри `<a>` вместо настоящей кнопки;
- Issue Form как разрешённый интерфейс записи;
- GitHub Actions как доверенный обработчик этого запроса;
- абсолютные raw-URL с явно указанной веткой;
- отдельные имена файлов для каждой темы;
- HTML `<p align="center">`, явные `width` и `height` для стабильной раскладки.

## Шаг 5. Создайте формы переключения тем

Для каждой темы создайте `.github/ISSUE_TEMPLATE/theme-<id>.yml`. Критически важен точный title:

```yaml
name: Use Mint Circuit theme
description: Switch the public profile to the mint color scheme
title: "[Profile Theme] Mint Circuit"
body:
  - type: checkboxes
    id: confirmation
    attributes:
      label: Confirmation
      options:
        - label: Switch the profile to Mint Circuit
          required: true
```

`resolve` принимает только issues с префиксом `[Profile Theme] ` и сопоставляет остаток title с полем `name` в JSON. Название должно совпадать посимвольно и быть уникальным.

Ссылка кнопки в README:

```html
<a href="https://github.com/<OWNER>/<REPO>/issues/new?template=theme-mint.yml">
  <!-- picture со сгенерированным SVG -->
</a>
```

Issue Forms хранятся в `.github/ISSUE_TEMPLATE`. Полная схема описана в [Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms).

## Шаг 6. Сгенерируйте кнопки тем

Запустите из корня репозитория:

```bash
python scripts/profile_theme.py apply violet
```

Команда:

1. валидирует выбранную тему;
2. заменяет маркер в README;
3. перекрашивает URL известных виджетов;
4. меняет Breakout и visits URL на выбранный theme id;
5. меняет имена SVG-кнопок в README;
6. создаёт матрицу кнопок для **каждой** активной темы, каждой целевой темы и обоих режимов;
7. обновляет `.github/profile-theme.json`.

При трёх темах создаются `3 × 3 × 2 = 18` файлов:

```text
.github/profile-theme-control-<active>-<target>.svg
.github/profile-theme-control-<active>-<target>-dark.svg
```

В имени есть и активная, и целевая тема. Выбранная кнопка получает accent-фон и верхний индикатор. README с темой `violet` ссылается только на строку файлов `profile-theme-control-violet-*`, но остальные строки заранее готовы для следующего переключения.

Проверьте изменения перед первым коммитом:

```bash
git diff -- README.md .github/profile-theme.json
git status --short
```

## Шаг 7. Настройте workflow

Используйте `.github/workflows/change-profile-theme.yml`. Текущие триггеры:

```yaml
on:
  issues:
    types: [opened]
  schedule:
    - cron: "15 */12 * * *"
  workflow_dispatch:
  push:
    branches: [main]
```

Назначение запусков:

- `issues` — применить запрошенную тему, обновить артефакты, закоммитить и удалить issue;
- `schedule` — обновить contribution graph и visits snapshot;
- `workflow_dispatch` — ручная регенерация;
- `push` в `main` — синхронизация артефактов после изменения исходников.

Job получает минимально необходимое встроенному токену право:

```yaml
permissions:
  contents: write
```

Оно позволяет `GITHUB_TOKEN` публиковать `pacman-output` и делать bot-коммит в `main`. GitHub создаёт этот токен автоматически; добавлять его в Secrets вручную не нужно. Подробнее: [Use GITHUB_TOKEN for authentication in workflows](https://docs.github.com/actions/how-tos/security-for-github-actions/security-guides/automatic-token-authentication).

Concurrency-группа `profile-theme-and-breakout` с `cancel-in-progress: false` не отменяет уже начатую смену темы, а ставит следующий запуск в очередь.

### Генерация Breakout

Action:

```yaml
- uses: abozanona/pacman-contribution-graph@main
  with:
    github_user_name: ${{ github.repository_owner }}
    games: breakout
    hide_month_labels: true
```

создаёт:

```text
dist/breakout-contribution-graph.svg
dist/breakout-contribution-graph-dark.svg
```

Workflow копирует базовую пару для каждой темы, затем выполняет:

```bash
python scripts/profile_theme.py recolor-breakout --theme-id "$theme" "$light" "$dark"
python scripts/profile_theme.py verify-breakout --theme-id "$theme" "$light" "$dark"
```

Перекраска заменяет пять стандартных GitHub-цветов:

| Режим | Исходная шкала |
|---|---|
| light | `EBEDF0`, `9BE9A8`, `40C463`, `30A14E`, `216E39` |
| dark | `161B22`, `0E4429`, `006D32`, `26A641`, `39D353` |

на пять значений `breakout` выбранной палитры. Проверка требует, чтобы исходные цвета исчезли и хотя бы один тематический цвет присутствовал. После создания тематических файлов исходная generic-пара удаляется из `dist`.

> Скрипт полагается на текущую цветовую шкалу generator Action. Если upstream изменит цвета или формат SVG, проверка намеренно завершит workflow с ошибкой вместо публикации частично перекрашенного графика.

### Генерация visits

Workflow получает SVG Komarev:

```bash
curl --fail --silent --show-error \
  "https://komarev.com/ghpvc/?username=<USERNAME>&abbreviated=true" \
  --output profile-visits-counter.svg
```

Затем:

```bash
python scripts/profile_theme.py generate-visits \
  --visits-svg profile-visits-counter.svg \
  --output-dir dist
```

`extract_visits()` разбирает SVG как XML, собирает текстовые узлы, похожие на число (`1,234`, `12.3K`, `2M`), и использует последний. `write_visits_cards()` создаёт для каждой темы light/dark-карточку `165 × 195`.

Это **снимок внешнего счётчика**, а не GitHub Analytics. Он обновляется только при запуске workflow. Кроме того, запрос самого workflow может влиять на показание в зависимости от правил Komarev, поэтому число следует считать приблизительным, а не аудиторской метрикой уникальных посетителей.

## Шаг 8. Настройте ветку артефактов

Workflow публикует весь `dist` через:

```yaml
- uses: crazy-max/ghaction-github-pages@v3.1.0
  with:
    build_dir: dist
    target_branch: pacman-output
    keep_history: true
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Создавать `pacman-output` вручную обычно не требуется: Action создаст её при первой успешной публикации. `keep_history: true` сохраняет историю публикаций. Не редактируйте эту ветку вручную — следующий запуск считает `dist` источником истины.

Текущий репозиторий также содержит:

- `.github/workflows/pacman.yml`, публикующий Pac-Man SVG в `pacman-output`;
- `.github/workflows/snake.yml`, публикующий `snake.svg` в отдельную ветку `output`;
- ветку `output`, оставшуюся от прежней версии README.

Для воспроизведения **текущего видимого профиля** они не нужны: актуальный README использует Breakout и visits из `pacman-output`. Если вы всё же оставляете `pacman.yml`, учтите, что два workflow публикуют в одну ветку, но используют разные concurrency-группы; одновременные push могут конфликтовать. Надёжнее оставить один объединённый workflow или дать обоим одну concurrency-группу.

## Шаг 9. Настройте токены и секреты

### Встроенный `GITHUB_TOKEN`

Для публикации и коммита используется автоматический `${{ secrets.GITHUB_TOKEN }}`. Проверьте:

1. **Settings → Actions → General**.
2. В **Workflow permissions** разрешите read/write, если политика аккаунта не позволяет job-level `contents: write` повысить доступ.
3. Если `main` защищена, разрешите GitHub Actions обходить нужные правила либо замените прямой push на pull request.

Принцип минимальных прав важен: workflow не нужны глобальные права `write-all`.

### `PROFILE_ADMIN_TOKEN`

Отдельный секрет нужен только для финального GraphQL `deleteIssue`. Встроенный токен используется для содержимого, а удаление issue выполняется токеном владельца/администратора.

Рекомендуемый вариант — fine-grained personal access token:

1. Откройте **Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
2. Выберите себя как resource owner.
3. Ограничьте **Repository access** только профильным репозиторием.
4. Выдайте repository permission **Issues: Read and write**; `Metadata: Read` добавляется как базовое право.
5. Задайте короткий срок действия и создайте токен.
6. В репозитории откройте **Settings → Secrets and variables → Actions → New repository secret**.
7. Имя секрета: `PROFILE_ADMIN_TOKEN`.
8. Значение: созданный PAT.

Документация: [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) и [Secrets in GitHub Actions](https://docs.github.com/en/actions/concepts/security/secrets).

Если GraphQL `deleteIssue` не поддерживает fine-grained PAT для вашего типа аккаунта или политики, используйте classic PAT с минимальным подходящим доступом к публичному репозиторию (`public_repo`) и правами администратора самого владельца. Это более широкий токен: ограничьте срок, храните только в Actions Secrets и немедленно отзовите при утечке.

Никогда не записывайте PAT в YAML, README, shell history или Git. Секрет невозможно прочитать обратно через интерфейс после сохранения — его можно только заменить.

Удаление issue не обязательно для смены темы. Если оно вам не нужно, удалите шаг `Delete service theme issue` и секрет `PROFILE_ADMIN_TOKEN`; переключение будет работать, но служебные issues останутся в репозитории.

## Шаг 10. Разберитесь с кэшем raw.githubusercontent.com

Ветка в raw-URL — подвижная ссылка:

```text
https://raw.githubusercontent.com/<OWNER>/<REPO>/pacman-output/<FILE>.svg
```

`raw.githubusercontent.com` может кэшировать файл по branch-based URL примерно пять минут. В текущей реализации query parameters (`?v=...`, `?game=...`) не считаются надёжным cache-buster: скрипт намеренно удаляет query у Breakout URL.

Обход — **менять pathname**:

```text
breakout-contribution-graph-violet.svg
breakout-contribution-graph-mint.svg
profile-visits-violet.svg
profile-visits-mint.svg
profile-theme-control-violet-mint.svg
profile-theme-control-mint-mint.svg
```

При смене темы README начинает запрашивать другое имя файла, поэтому старый объект кэша не мешает. Это одна из причин генерировать артефакты для всех тем заранее.

Плановый запуск обновляет файл с тем же именем, поэтому небольшой лаг raw-кэша всё равно возможен. Если требуется строго неизменяемый результат, используйте URL с commit SHA, но тогда workflow должен обновлять README после каждой генерации.

## Шаг 11. Первичная публикация

До того как README начнёт ссылаться на `pacman-output`, выполните первичный запуск:

1. Закоммитьте исходники и сгенерированные управляющие SVG в `main`.
2. Откройте вкладку **Actions**.
3. Выберите **Update profile theme and Breakout**.
4. Запустите **Run workflow**.
5. Дождитесь создания `pacman-output`.
6. Проверьте raw-URL нужной темы.

Пример ожидаемых файлов:

```text
breakout-contribution-graph-graphite.svg
breakout-contribution-graph-graphite-dark.svg
breakout-contribution-graph-mint.svg
breakout-contribution-graph-mint-dark.svg
breakout-contribution-graph-violet.svg
breakout-contribution-graph-violet-dark.svg
profile-visits-graphite.svg
profile-visits-graphite-dark.svg
profile-visits-mint.svg
profile-visits-mint-dark.svg
profile-visits-violet.svg
profile-visits-violet-dark.svg
```

Проверочный шаг workflow читает тематические файлы не через raw CDN, а через GitHub Contents API с заголовком `Accept: application/vnd.github.raw+json`. Для Breakout предусмотрено до пяти попыток с паузой две секунды, затем запускается `verify-breakout`. Visits-файлы проверяются по наличию строки `GitHub visits`.

## Алгоритм смены темы

Пользовательский сценарий:

1. Нажмите вертикальную кнопку темы в README.
2. GitHub откроет соответствующую Issue Form.
3. Отметьте обязательный checkbox.
4. Создайте issue, не меняя предзаполненный title.
5. Workflow применит тему и удалит issue после успеха.

Программный сценарий для локальной проверки:

```bash
python scripts/profile_theme.py resolve \
  --event-name issues \
  --issue-title "[Profile Theme] Mint Circuit"
```

Ожидаемый вывод:

```text
id=mint
```

При `schedule`, `push` и `workflow_dispatch` команда `resolve` игнорирует title и возвращает `active` из `.github/profile-theme.json`. `apply` выполняется только для события `issues`; плановые запуски не переписывают README.

## Как добавить четвёртую тему

1. Скопируйте существующий JSON в `.github/profile-themes/<new-id>.json`.
2. Задайте уникальные `id`, `name`, light/dark токены и обе пятицветные Breakout-шкалы.
3. Создайте `.github/ISSUE_TEMPLATE/theme-<new-id>.yml` с title `[Profile Theme] <точное name>`.
4. Добавьте ссылку-кнопку в блок controls в README.
5. Выполните `python scripts/profile_theme.py apply <текущая-тема>` — это пересоздаст всю матрицу SVG.
6. Проверьте, что новые файлы добавлены в Git.
7. Запустите workflow вручную, чтобы `pacman-output` получил Breakout и visits для новой темы.
8. Только после успешной публикации проверяйте переключение через issue.

Список тем не захардкожен в скрипте: он строится по `.github/profile-themes/*.json`. Однако HTML-ссылки в README добавляются вручную.

## Локальная проверка

### Проверка синтаксиса Python

```bash
python -m py_compile scripts/profile_theme.py
```

### Проверка resolver

```bash
python scripts/profile_theme.py resolve --event-name workflow_dispatch
python scripts/profile_theme.py resolve --event-name issues --issue-title "[Profile Theme] Graphite Alloy"
python scripts/profile_theme.py resolve --event-name issues --issue-title "[Profile Theme] Mint Circuit"
python scripts/profile_theme.py resolve --event-name issues --issue-title "[Profile Theme] Violet Dusk"
```

### Безопасная проверка `apply`

`apply` изменяет README, state и SVG в рабочем дереве. Выполняйте его в чистом временном клоне или сначала убедитесь, что нужные изменения закоммичены:

```bash
git status --short
python scripts/profile_theme.py apply graphite
git diff --check
git diff -- README.md .github/profile-theme.json
```

Проверьте оба режима в GitHub, а не только в локальном Markdown preview: разные рендереры по-разному санитизируют HTML и обрабатывают `<picture>`.

### Проверка Breakout на реальных артефактах

После генерации Action или скачивания SVG:

```bash
python scripts/profile_theme.py recolor-breakout \
  --theme-id violet \
  dist/breakout-contribution-graph-violet.svg \
  dist/breakout-contribution-graph-violet-dark.svg

python scripts/profile_theme.py verify-breakout \
  --theme-id violet \
  dist/breakout-contribution-graph-violet.svg \
  dist/breakout-contribution-graph-violet-dark.svg
```

### Финальный чек-лист

- [ ] Репозиторий публичный и называется как GitHub username.
- [ ] В README ровно один `profile-theme` marker.
- [ ] Все username/repository URL заменены.
- [ ] Все JSON-темы проходят `load_theme` через `apply` или `resolve`.
- [ ] Каждая тема имеет Issue Form с точным title.
- [ ] Сгенерированы light/dark controls для всех пар тем.
- [ ] Actions имеют `contents: write`.
- [ ] Секрет `PROFILE_ADMIN_TOKEN` создан или шаг удаления issue отключён.
- [ ] Первый workflow создал `pacman-output`.
- [ ] Breakout и visits доступны через GitHub API и raw URL.
- [ ] README проверен в светлом и тёмном режиме.
- [ ] Клик по каждой кнопке открывает правильный шаблон.
- [ ] Тестовый issue меняет тему и после успеха удаляется.

## Troubleshooting

### README не отображается на профиле

Проверьте, что репозиторий публичный, его имя совпадает с username, а непустой `README.md` находится в корне default branch.

### Workflow не запускается после создания issue

Проверьте:

- Issues включены в Settings;
- issue действительно создан, а не оставлен в preview;
- title начинается с `[Profile Theme] `;
- job-level условие не отфильтровало событие;
- workflow уже существовал в default branch на момент события.

### `Unsupported issue title` или `Unknown ... profile theme name`

Не редактируйте title формы. Сравните его часть после префикса с `name` в JSON. Имена чувствительны к пробелам и регистру. Также проверьте отсутствие двух JSON с одинаковым `name`.

### `Invalid theme id`, `Unknown theme` или `Theme id mismatch`

Используйте только `[a-z0-9-]`, убедитесь, что имя `<id>.json` совпадает с полем `id`, а файл находится в `.github/profile-themes`.

### `palette is missing` или `must contain 5 colors`

Добавьте все обязательные токены в обе палитры. В `breakout` должно быть ровно пять значений без `#`.

### `README profile-theme marker is missing or duplicated`

Оставьте ровно одну строку вида:

```markdown
<!-- profile-theme: violet -->
```

### Breakout остался зелёным

Возможные причины:

- upstream generator изменил стандартные цвета;
- переданы generic-файлы с неожиданными именами;
- dark-файл не содержит `-dark` в stem, поэтому выбран light mapping;
- README показывает закэшированное старое имя.

Откройте SVG как текст, сравните цвета с `LIGHT_SOURCE`/`DARK_SOURCE` и запустите `verify-breakout`.

### `was not fully recolored`

Сообщение показывает оставшиеся исходные цвета и найденные тематические цвета. Если source цвета поменялись upstream, обновите константы только после визуальной проверки новой пятиуровневой шкалы.

### `Could not extract profile visits`

Komarev мог изменить SVG, вернуть HTML ошибки или challenge page. Проверьте:

```bash
file profile-visits-counter.svg
head -n 20 profile-visits-counter.svg
```

Убедитесь, что это валидный XML/SVG и в текстовом узле есть число. Не ослабляйте регулярное выражение до произвольного текста: иначе на карточку может попасть служебная строка.

### `PROFILE_ADMIN_TOKEN is not configured`

Создайте repository Actions secret с точным именем. Environment secret не будет доступен job без соответствующего `environment:`.

### GraphQL не удаляет issue

Проверьте срок действия PAT, доступ именно к этому репозиторию, permission Issues read/write и административные права владельца токена. Если удаление не принципиально, отключите только последний шаг — основная смена темы уже завершена раньше.

### Push в `main` отклонён

Причины обычно две:

- у `GITHUB_TOKEN` read-only policy;
- branch protection/ruleset запрещает прямой bot-push.

Разрешите нужное исключение для Actions либо измените процесс на PR. Не заменяйте встроенный токен широким PAT без необходимости.

### SVG опубликован, но README показывает старую тему

Проверьте, изменилось ли имя файла в HTML. Query string не считается надёжным обходом raw-кэша. Подождите несколько минут, сделайте hard refresh и откройте новый pathname напрямую.

### Dark-картинка получает light-палитру

Убедитесь, что dark URL находится на той же строке, где есть `prefers-color-scheme: dark`. Это особенность построчного алгоритма `apply_theme()`.

### Кнопка темы не меняет тему сразу

Кнопка только открывает форму. Пользователь должен подтвердить checkbox и создать issue; затем требуется время на Actions run и распространение raw-кэша.

### Два workflow конфликтуют при публикации

Не запускайте независимые publishers одной ветки с разными concurrency-группами. Объедините генераторы в один workflow или используйте общую группу. Это особенно важно, если вы сохранили отдельный `pacman.yml`.

## Эксплуатация и безопасность

- Закрепляйте сторонние Actions на commit SHA для более строгой защиты supply chain; текущая реализация использует `@main` для generator и version tag для publisher.
- Dependabot может отслеживать GitHub Actions и предлагать обновления.
- Регулярно обновляйте или ротируйте `PROFILE_ADMIN_TOKEN`.
- Считайте содержимое issue недоверенным вводом. Текущий resolver принимает только фиксированный префикс и точное имя известной темы, а theme id валидирует регулярным выражением.
- Не подставляйте issue body в shell-команды.
- Сохраняйте `timeout-minutes`, чтобы зависший сторонний сервис не занимал runner бесконечно.
- Периодически проверяйте доступность внешних карточек; отказ Vercel/Komarev не должен ломать остальной профиль.
- Не удаляйте старые документы или схемы темы без миграции ссылок: raw-кэш и старые коммиты могут ещё ссылаться на них.

## Внешние ссылки

- [GitHub: Managing your profile README](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)
- [GitHub: Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub: Use GITHUB_TOKEN for authentication](https://docs.github.com/actions/how-tos/security-for-github-actions/security-guides/automatic-token-authentication)
- [GitHub: Secrets](https://docs.github.com/en/actions/concepts/security/secrets)
- [GitHub: Managing personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub: Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [GitHub: Contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)
- [GitHub: REST repository contents](https://docs.github.com/en/rest/repos/contents)
- [GitHub: Secure use reference for Actions](https://docs.github.com/en/actions/reference/security/secure-use)
- [abozanona/pacman-contribution-graph](https://github.com/abozanona/pacman-contribution-graph)
- [crazy-max/ghaction-github-pages](https://github.com/crazy-max/ghaction-github-pages)
- [Komarev GitHub Profile Views Counter](https://github.com/antonkomarev/github-profile-views-counter)
- [GitHub Profile Summary Cards](https://github.com/vn7n24fzkq/github-profile-summary-cards)
- [GitHub Readme Streak Stats](https://github.com/DenverCoder1/github-readme-streak-stats)
- [Readme Typing SVG](https://github.com/DenverCoder1/readme-typing-svg)
- [Capsule Render](https://github.com/kyechan99/capsule-render)

## Краткая модель сопровождения

`main` — единственный источник истины для темы и README. JSON определяет дизайн, Python применяет его детерминированно, Issue Form передаёт только выбор, Actions генерирует и проверяет артефакты, а `pacman-output` служит публикационной веткой. Если сохранять это разделение, добавление тем и виджетов остаётся предсказуемым, а сбой внешнего генератора обнаруживается до того, как README переключится на неготовые файлы.
