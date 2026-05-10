# Library YAML Format

This document describes the YAML files used by `bcp library`. It is written for
people maintaining their own reading library and for agents that convert pasted
content into files `daily-bcp` can read.

The format below documents the current parser in `bcp_cli/data.py`. It is a
narrow YAML subset, not a general-purpose YAML schema.

## Location And File Names

Library files live in the library folder shown by:

```sh
bcp library --path
```

By default, that folder is beside the notes file. It can be overridden with
`BCP_LIBRARY_DIR`.

Each library item is one `.yaml` file. The filename stem is the command key:

```text
item1.yaml      -> bcp library item1
sample.yaml     -> bcp library sample
rule_of_life.yaml -> bcp library rule_of_life
```

Use a filename stem only. Do not use path separators in a library key.

## Required Shape

Every library file must have this structure:

```yaml
title: Item Title
readings:
  reading_key:
    title: Reading Title
    text: |
      Reading text here.
```

Required fields:

- `title`: the title of the whole library item.
- `readings`: a mapping of one or more readings.
- Each reading has a key, such as `first`, `augustine`, or `chapter_1`.
- Each reading must contain `title`.
- Each reading must contain `text: |` followed by an indented literal block.

## Valid Example

```yaml
title: Sample Devotional Readings
readings:
  augustine:
    title: Augustine, Confessions, Book I.1
    text: |
      Source: Augustine of Hippo, Confessions, Book I, Chapter 1.
      https://en.wikisource.org/wiki/Nicene_and_Post-Nicene_Fathers:_Series_I/Volume_I/Confessions/Book_I/Chapter_1

      Great art Thou, O Lord, and greatly to be praised; great is Thy power,
      and of Thy wisdom there is no end.

  bernard:
    title: Bernard, On Loving God, Chapter IX
    text: |
      Source: Bernard of Clairvaux, On Loving God, Chapter IX.
      https://www.ccel.org/ccel/bernard/loving_god.xi.html

      So then in the beginning man loves God, not for God's sake, but for his
      own.
```

## Parser Rules

The current parser expects this exact style:

- Top-level keys are `title` and `readings`.
- Reading entries are indented two spaces under `readings`.
- Reading fields are indented four spaces under the reading key.
- Text body lines are indented six spaces under `text: |`.
- Reading text must use a literal block: `text: |`.
- Blank lines inside `text` are preserved when they appear in the literal block.
- Quoted scalar titles are accepted, but plain titles are preferred.

Unsupported features:

- Extra top-level keys, such as `author`, `source`, `tags`, or `date`.
- Extra reading fields besides `title` and `text`.
- YAML lists.
- Front matter markers such as `---`.
- Inline reading text, such as `text: Reading text here.`
- Folded text blocks, such as `text: >`.
- Arbitrary nested metadata.

If a source, author, URL, or citation is important, put it at the top of the
reading's `text` block.

## Agent Conversion Rules

When converting pasted content into library YAML:

1. Create one `.yaml` file per library item.
2. Use the item's display title as the top-level `title`.
3. Choose stable lowercase `snake_case` reading keys.
4. Preserve the source text exactly where possible.
5. Put source lines, attribution, and URLs inside the `text` block.
6. Use `text: |` for every reading body.
7. Do not add unsupported fields.
8. Keep indentation exactly as shown in the examples.

Good reading keys:

```text
first
second
augustine
chapter_1
morning_prayer
```

Avoid keys with spaces, slashes, or punctuation:

```text
Chapter 1
chapter/1
chapter:1
```

## Agent Prompt

You can give an agent a prompt like this:

```text
Convert the following content into daily-bcp library YAML.

Rules:
- Use this exact shape:
  title: Item Title
  readings:
    reading_key:
      title: Reading Title
      text: |
        Reading text here.
- Use lowercase snake_case reading keys.
- Put source, author, and URL lines inside the text block.
- Preserve paragraph breaks.
- Do not add unsupported fields.

Content:
...
```
