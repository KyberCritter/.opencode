# Markdown Authoring Guidelines

Follow these rules whenever creating or editing markdown files, or writing markdown-formatted output.

## Rules

- Always specify language on code blocks - Use `bash`, `yaml`, `json`, `text`, `hcl`, `go`, etc. Never use bare ` ``` `
- Use headings, not bold for section titles - Use proper heading levels (`##`, `###`, etc.) not `**Bold**` on its own line
- One H1 per file - Only one `# Title` at the top
- First line should be H1 - Start files with `# Title`
- Always include a single trailing newline so the file ends in a blank line
- Always add an empty line between different markdown styles (paragraphs, headings, lists, code blocks, block quotes, etc.)
- Use numbered lists only when order is meaningful (steps, sequences) - Use `-` for everything else
- Use `-` for unordered lists - Never use `*` or `+` as the bullet character
- Use inline links `[text](path)` - Never leave a bare URL in prose. Use relative paths for files within the repo
- Tables need a header row and a separator row - Use tables for reference data, use lists for procedural steps
- Use `**bold**` only for critical requirements and key terms on first use, use `_italic_` sparingly for titles or soft emphasis. Never use either for decoration
- Never use horizontal rules (`---`)

## Examples

### Code Blocks

Always specify language.

CORRECT:

```bash
#!/bin/bash
```

INCORRECT:

```text
#!/bin/bash
```

### Headings vs Bold

INCORRECT:

```text
**Status: Not Implemented**
Some description...
```

CORRECT:

```text
### Status

Not Implemented

Some description...
```

### Trailing New Line

INCORRECT:

```text
The End.```
```

CORRECT:

```text
The End.

```

### Empty Line Between Markdown Styles

INCORRECT:

```text
## Hello
There
```

CORRECT:

```text
## Hello

There
```

INCORRECT:

```text
Hello there
- thing 1
- thing 2
```

CORRECT:

```text
Hello there

- thing 1
- thing 2
```

### List Bullet Character

INCORRECT:

```text
* thing 1
* thing 2
```

```text
+ thing 1
+ thing 2
```

CORRECT:

```text
- thing 1
- thing 2
```

### Numbered vs Unordered Lists

Numbered lists are for sequences where order matters. Everything else uses `-`.

INCORRECT:

```text
1. Milk
2. Eggs
3. Bread
```

CORRECT:

```text
- Milk
- Eggs
- Bread
```

```text
1. Install dependencies
2. Run migrations
3. Start the server
```

### Links

INCORRECT:

```text
See https://example.com/docs/setup for details.
```

CORRECT:

```text
See the [setup guide](https://example.com/docs/setup) for details.
```

Relative paths for in-repo files:

```text
See [implementation-plan.md](docs/implementation-plan.md) for the rationale.
```

### Tables

Tables need a header row and a separator row. Use tables for reference data, lists for procedural steps.

INCORRECT:

```text
Name: foo, Type: string
Name: bar, Type: int
```

CORRECT:

```text
| Name | Type   |
| ---- | ------ |
| foo  | string |
| bar  | int    |
```

### Emphasis

INCORRECT:

```text
This is **very important** and you should **really** pay attention.
```

CORRECT:

```text
**Never** commit secrets to the repository.

Run the `_setup` script before continuing.
```

### Tone

INCORRECT:

```text
This awesome function magically handles all your validation needs!
The API might return an error sometimes.
```

CORRECT:

```text
Validate input before passing it to the handler.
The API returns an error when the payload is malformed.
```

### Horizontal Rules

INCORRECT:

```text
## Section One

Content here.

---

## Section Two

Content here.
```

CORRECT:

```text
## Section One

Content here.

## Section Two

Content here.
```
