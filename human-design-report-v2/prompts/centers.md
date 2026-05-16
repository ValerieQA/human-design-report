Write section: 🧠 Centers in {report_language}.
First inspect chart_json.centers.
If all values are null/empty, output exactly:
Center data was not available in the source PDF, so this section cannot be interpreted reliably from the current file.
Otherwise interpret only centers with actual source values.
Do not infer unavailable center states. No markdown symbols.

Chart JSON:
{chart_json}
