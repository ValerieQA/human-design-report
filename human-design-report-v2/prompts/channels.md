Write section: 🔗 Channels in {report_language}.

First inspect chart_json.channels.
- If channels list is empty, output exactly:
Channel data was not available or was not extracted from the source PDF, so this section should be treated as unavailable.
- Otherwise, interpret only listed channels from source JSON.

Use practical language and short bullets.
Do not add channels that are not in source JSON.
Plain text labels only, no markdown symbols.

Chart JSON:
{chart_json}
