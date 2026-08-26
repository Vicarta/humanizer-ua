# 🇺🇦 humanizer-ua

Текст може бути граматично правильним і все одно звучати так, ніби його
склали за шаблоном. `humanizer-ua` допомагає Codex і Claude редагувати
українські тексти природніше: прибирає канцелярит, кальки та рівний машинний
ритм, але не чіпає факти й авторську думку.

Це навичка для редагування готового тексту, а не генератор «людських помилок».
Вона не додає вигаданих історій, цифр або цитат і не обіцяє пройти
AI-детектори.

## Що вміє

- повністю редагувати український текст;
- проводити аудит без переписування;
- виправляти лише обрану проблему, наприклад канцелярит або кальки;
- підлаштовуватися під зразки авторського голосу;
- перевіряти лексику, ритм і структуру локальним сканером.

В основі навички 42 патерни в 11 категоріях і 20 сильних маркерів. Факт-замок
захищає імена, числа, дати, цитати, джерела, умови та висновки від випадкової
підміни під час редагування.

## Спробувати за хвилину

Після встановлення дайте Codex або Claude готовий український текст:

```text
Перепиши природною українською, але не змінюй факти: ...
Перевір цей текст на AI-маркери й нічого не редагуй: ...
Прибери лише канцелярит: ...
```

У Codex навичку можна викликати явно: `$humanizer-ua`. Плагін Claude Code
також додає команди `/humanize` та `/audit`.

## Встановлення в Claude

### Claude Code через marketplace

```text
/plugin marketplace add Vicarta/humanizer-ua
/plugin install humanizer-ua@vicarta-plugins
```

### Claude Code вручну

```bash
git clone https://github.com/Vicarta/humanizer-ua.git
mkdir -p ~/.claude/skills
cp -R humanizer-ua/skills/humanizer-ua ~/.claude/skills/
```

### Claude.ai

Зберіть ZIP із кореня репозиторію:

```bash
python3 scripts/build_release_zip.py
```

Потім завантажте `dist/humanizer-ua.zip` через **Settings → Capabilities →
Skills → Upload skill**.

## Встановлення в Codex

```bash
git clone https://github.com/Vicarta/humanizer-ua.git
mkdir -p ~/.codex/skills
cp -R humanizer-ua/skills/humanizer-ua ~/.codex/skills/
```

Для одного проєкту скопіюйте папку навички в
`.codex/skills/humanizer-ua`. Після встановлення перезапустіть Codex.

## Локальний сканер

Сканер працює без сторонніх Python-пакетів:

```bash
python3 skills/humanizer-ua/scripts/scan.py article.txt
python3 skills/humanizer-ua/scripts/scan.py article.txt --genre academic
python3 skills/humanizer-ua/scripts/scan.py article.txt --json
```

Підтримувані жанри: `marketing`, `neutral`, `academic`, `legal`, `fiction`.
Код завершення `1` означає, що сканер знайшов сильні маркери; `0` означає, що
їх немає.

Оцінка сканера показує щільність редакторських сигналів. Це не визначення
авторства й не ймовірність того, що текст створила модель.

## Для розробників

```bash
python3 scripts/lint_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/build_release_zip.py
python3 scripts/install_smoke.py --zip dist/humanizer-ua.zip
```

## Походження та ліцензія

Проєкт створено на основі
[`ilyautov/humanizer-ru`](https://github.com/ilyautov/humanizer-ru) за ліцензією
MIT. Це окрема українська адаптація: мовний каталог, сканер і тести написано
заново. Атрибуцію та опис відмінностей див. у [NOTICE.md](NOTICE.md).
