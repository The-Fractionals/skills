# Claude Code Skills

Custom skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that extend Claude's capabilities with domain-specific expertise.

## Skills

### Executive CV

Create professional, ATS-friendly executive CVs for C-suite and senior leadership roles (CTO, CEO, COO, CFO, CIO, Director, NED) following UK best practice. Outputs a formatted .docx file.

**Features:**
- UK executive CV conventions (2-page, no photo, reverse chronological)
- Achievement bullet formula: Action + Scope + Quantified Outcome
- Optional EVR (Environment-Vision-Resources) narrative framework
- Role-specific guidance for CTO, CEO, COO, CFO
- Discovery questions to extract strategic impact from candidates

[View skill &rarr;](executive-cv/)

## Installation

### Claude Code (CLI)

Add a skill to your project:

```bash
claude skill add /path/to/skills/executive-cv
```

Or add as a user-level skill available across all projects:

```bash
claude skill add --user /path/to/skills/executive-cv
```

### Claude Desktop / Cowork

Copy the contents of the skill's `SKILL.md` into your project instructions, or reference the file path directly.

## Requirements

- Access to the `docx` skill (built-in on Claude Code)

## Licence

[MIT](LICENSE)
