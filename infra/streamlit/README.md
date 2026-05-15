# Streamlit Community Cloud Profile

This profile is for the hosted hackathon demo.

1. Push the repository to public GitHub.
2. Deploy with Streamlit Community Cloud.
3. Select `app/streamlit_app.py` as the main file path.
4. Keep root `requirements.txt` pointing at `infra/streamlit/requirements.txt`.
5. Keep `.streamlit/config.toml` mirrored from `infra/streamlit/streamlit_config.toml`.
6. No secrets are required.
7. Use the bundled demo repo during the live demo.

Validate the mirrored config before deployment:

```bash
make check-cloud-config
```
