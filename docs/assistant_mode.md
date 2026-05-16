# AI Assistant Mode

## Overview

RepoQuest includes an **optional AI assistant** powered by Claude that can provide additional insights beyond deterministic static analysis.

**Important:** The AI assistant is:
- **Disabled by default**
- **Optional** - all core RepoQuest features work without it
- **Manual-only** - never runs automatically
- **Bounded** - only receives capped context packs, not entire repos
- **Safe** - validates responses to prevent execution claims

## Configuration

### Environment Variables

Create a `.env` file (not tracked in git):

```bash
cp .env.example .env

# Enable AI assistant (default: false)
REPOQUEST_AI_ENABLED=true

# Claude API key (required if enabled)
CLAUDE_API_KEY=your_api_key_here

# Claude model (optional, default: claude-sonnet-4-20250514)
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### Streamlit Secrets (Cloud Deployment)

For Streamlit Community Cloud, add secrets in the dashboard:

```toml
REPOQUEST_AI_ENABLED = "true"
CLAUDE_API_KEY = "your_api_key_here"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
```

If `REPOQUEST_AI_ENABLED=true` is set while no API key is available, RepoQuest keeps deterministic analysis enabled and shows a "no API key configured" assistant status.

## Features

When enabled, AI assistant buttons appear in these sections:

### 1. Overview Tab
- **Button:** "Get AI Insights on Overview"
- **Context:** Project type, frameworks, entry points, key folders
- **Output:** High-level analysis and recommendations

### 2. Architecture Map Tab
- **Button:** "Ask AI about this file" (after selecting a graph node)
- **Context:** Selected file metadata, imports, routes, tests, and snippets
- **Output:** Node-specific explanation and follow-up suggestions

### 3. Reading Path Tab
- **Button:** "Ask AI to explain..." (per reading path file)
- **Context:** File role, capped source preview, and detected routes where relevant
- **Output:** File explanation, risks, and improvement ideas

### 4. Components Tab
- **Button:** Component-specific assistant action
- **Context:** Component role, connections, detected items
- **Output:** Component-specific insights and improvement ideas

### 5. Tests Tab
- **Button:** "Get Test Recommendations"
- **Context:** Test inventory, coverage gaps, quality signals
- **Output:** Prioritized test suggestions

### 6. Work Plans Tab
- **Button:** "Refine Work Plan"
- **Context:** Generated tasks, workflows, milestones
- **Output:** Enhanced task descriptions and priorities

### 7. Documentation and Export Tabs
- **Button:** "Improve Documentation"
- **Context:** Existing docs, detected gaps
- **Output:** Documentation enhancement suggestions

## Safety Features

### Response Validation

All AI responses are validated to ensure:

1. **Non-empty responses** - Rejects blank outputs
2. **Valid file citations** - Only cites files that exist in the scanned repo
3. **No execution claims** - Rejects responses claiming tests were run
4. **No execution instructions** - Rejects responses instructing code execution

### Context Limits

AI requests are bounded:

- **Max snippet size:** 800 characters per file
- **Max files:** Limited by section (typically 5-10)
- **Safe files only:** Excludes `.env`, secrets, binaries
- **Static analysis warning:** Every request includes a disclaimer

### Example Validation

Rejected:
```
"I ran the tests and they all passed."
```

Accepted:
```
"Based on static analysis of backend/routes/trips.py,
the route handlers appear to lack input validation."
```

## Architecture

### Provider Pattern

```python
class AssistantProvider(Protocol):
  def generate(request: AssistantRequest) -> AssistantResponse:
   ...
```

**Implementations:**
- `DisabledAssistantProvider` - Returns "disabled"status
- `MockAssistantProvider` - Returns deterministic test responses
- `ClaudeAssistantProvider` - Calls Claude API via stdlib urllib

### Context Builders

Each section has a dedicated context builder:

- `build_overview_context()` - Project summary
- `build_file_context()` - Single file analysis
- `build_component_context()` - Component card analysis
- `build_test_context()` - Test intelligence
- `build_workflow_context()` - Work plan refinement
- `build_documentation_context()` - Doc enhancement

### Data Flow

```
User clicks AI button
 -> Context builder creates AssistantRequest
 -> Provider generates AssistantResponse
 -> Validator checks response
 -> UI displays result or validation error
```

## Usage Guidelines

### When to Use AI Assistant

 **Good use cases:**
- Getting high-level project insights
- Understanding complex component relationships
- Prioritizing test coverage gaps
- Refining work plan descriptions
- Improving documentation clarity

 **Not suitable for:**
- Replacing deterministic analysis
- Executing code or tests
- Making production decisions
- Security audits
- Compliance validation

### Best Practices

1. **Review AI outputs** - Always validate suggestions against actual code
2. **Use deterministic first** - Generate the quest before using AI
3. **Cite evidence** - Check that AI citations reference real files
4. **Stay bounded** - AI only sees capped snippets, not full files
5. **Manual only** - AI never runs automatically during quest generation

## Cost Considerations

- **API calls:** Each AI button click = 1 Claude API call
- **Token usage:** Typically 500-1500 tokens per request
- **Pricing:** See Anthropic pricing for current rates
- **Free tier:** Deterministic RepoQuest is always free

## Troubleshooting

### AI Assistant Not Available

**Symptom:** Sidebar shows "AI Assistant is disabled"

**Solutions:**
1. Set `REPOQUEST_AI_ENABLED=true` in `.env`
2. Restart the Streamlit app
3. Check sidebar status panel

### API Key Not Configured

**Symptom:** Sidebar shows "AI Assistant enabled but no API key configured"

**Solutions:**
1. Set `CLAUDE_API_KEY` in `.env` or Streamlit secrets
2. Verify key is valid
3. Restart the app

### Validation Errors

**Symptom:** Warning message after AI response

**Common causes:**
- AI cited non-existent files -> Check file paths
- AI claimed test execution -> Regenerate with different phrasing
- Empty response -> Try again or check API status

## Development

### Adding New AI Features

1. Create context builder in `repoquest/assistant_context.py`
2. Add button in relevant tab in `app/streamlit_app.py`
3. Use `run_assistant()` helper function
4. Display result from `st.session_state["assistant_outputs"]`

### Testing

```bash
# Run assistant tests
pytest tests/test_assistant.py -v

# Test with mock provider
REPOQUEST_AI_ENABLED=true pytest tests/test_assistant.py
```

### Mock Provider for Testing

```python
from repoquest.assistant_provider import MockAssistantProvider

provider = MockAssistantProvider(
  mock_response="Test response",
  mock_citations=[AssistantCitation(file_path="test.py")]
)
```

## Comparison: Deterministic vs AI

| Feature | Deterministic | AI Assistant |
|---------|--------------|--------------|
| **Always available** | Yes | Requires API key |
| **Cost** | Free | API costs |
| **Speed** | Instant | Usually a few seconds |
| **Reproducible** | Yes | May vary |
| **Evidence-based** | Always | Validated citations |
| **Offline** | Yes | Requires network |
| **Privacy** | Local only | Warning: Sends snippets |

## Privacy & Data

### What Gets Sent to Claude

- Capped code snippets (max 800 chars each)
- File paths and roles
- Project type and framework names
- Detected routes and components
- **Never sent:** Full files, secrets, binaries, credentials

### Network And Certificates

The Claude provider uses the Python standard library HTTP client. When available, it uses the local `certifi` certificate bundle to avoid common macOS certificate-chain errors. Network or certificate failures are displayed as assistant errors and do not interrupt deterministic RepoQuest output.

### Data Retention

- RepoQuest does not store AI responses permanently
- Responses live in Streamlit session state only
- Claude API retention: See Anthropic privacy policy

## Future Enhancements

Potential future features (not yet implemented):

- Streaming responses for long outputs
- Multi-turn conversations
- Custom system prompts
- Alternative LLM providers
- Response caching
- Batch processing

## Support

For issues or questions:

1. Check this documentation
2. Review validation messages
3. Test with mock provider
4. Check Anthropic API status
5. Open GitHub issue with details

---

**Remember:** AI assistant is optional. RepoQuest's deterministic analysis is the foundation.
