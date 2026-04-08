# _AI_CONTEXT_INDEX — Background Knowledge Base

This directory should contain markdown files from [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project).

## How to Populate

```bash
git clone https://github.com/Leerrooy95/The_Regulated_Friction_Project.git /tmp/rfp
cp /tmp/rfp/_AI_CONTEXT_INDEX/*.md ./_AI_CONTEXT_INDEX/
```

The app loads these files as background context for the Claude analysis.
Without them, the tool still works — it just relies on the taxonomy alone.
