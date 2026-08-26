# humanizer-ua

Український редакторський skill для Codex і Claude. Він прибирає шаблонність,
канцелярит, кальки та інші ознаки безособового AI-тексту, не змінюючи факти й
не вигадуючи нової конкретики.

Проєкт створено на основі
[`ilyautov/humanizer-ru`](https://github.com/ilyautov/humanizer-ru) за ліцензією
MIT. Це окрема українська адаптація: мовний каталог і сканер написано заново.

## Що всередині

- 42 патерни в 11 категоріях і 20 сильних маркерів;
- режими повного редагування, аудиту без змін та точкової правки;
- калібрування під голос автора;
- факт-замок: числа, імена, дати, цитати й твердження не можна додавати або
  підміняти без джерела;
- офлайн-сканер для лексики, ритму й структури;
- пакування для Claude Code та Codex.

Сканер не визначає авторство і не обіцяє «обхід детекторів». Його оцінка
показує щільність редакторських сигналів, а не ймовірність того, що текст
створила модель.

## Встановлення в Codex

Скопіюйте папку навички в особистий або проєктний каталог:

```bash
git clone git@github.com:Vicarta/humanizer-ua.git
mkdir -p ~/.codex/skills
cp -R humanizer-ua/skills/humanizer-ua ~/.codex/skills/
```

Для одного репозиторію скопіюйте її в `.codex/skills/humanizer-ua` у корені
цього репозиторію. Після встановлення перезапустіть Codex. Явний виклик:
`$humanizer-ua`.

## Встановлення в Claude Code

Через plugin marketplace:

```text
/plugin marketplace add Vicarta/humanizer-ua
/plugin install humanizer-ua@vicarta-plugins
```

Або вручну:

```bash
mkdir -p ~/.claude/skills
cp -R humanizer-ua/skills/humanizer-ua ~/.claude/skills/
```

Плагін також додає команди `/humanize` та `/audit`.

## Використання

```text
Олюдни цей український текст: ...
Перепиши природною українською, але не змінюй факти: ...
Перевір текст на AI-маркери, нічого не редагуй: ...
Прибери лише канцелярит: ...
```

## Офлайн-сканер

```bash
python3 skills/humanizer-ua/scripts/scan.py article.txt
python3 skills/humanizer-ua/scripts/scan.py article.txt --genre academic
python3 skills/humanizer-ua/scripts/scan.py article.txt --json
```

Жанри: `marketing`, `neutral`, `academic`, `legal`, `fiction`. Код завершення
`1` означає, що знайдено сильні маркери; `0` - їх немає.

## Перевірка проєкту

```bash
python3 scripts/lint_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/build_release_zip.py
python3 scripts/install_smoke.py --zip dist/humanizer-ua.zip
```

## Ліцензія

MIT. Атрибуцію та опис відмінностей див. у [NOTICE.md](NOTICE.md).
