Write section: 🧠 Centers in {report_language}.

First inspect chart_json.centers.
- If all center values are null/empty, output exactly:
Center data was not available in the source PDF, so this section cannot be interpreted reliably.
- Otherwise, interpret only centers that have actual values from source JSON.

Use concise practical bullets and short paragraphs.
Do not invent missing center statuses.
Plain text labels only, no markdown symbols.

Chart JSON:
{chart_json}
