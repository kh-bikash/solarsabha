# AWS setup

1. Verify student profiles on AWS Builder Center (event requirement). Create the AWS account, enable MFA, set a small budget alert.
2. Bedrock console (region ap-south-1 or the region you choose): request/enable a model that supports images and documents. Note its model id or inference profile id. Set `BEDROCK_MODEL_ID`. Availability varies by account and region: check.
3. Local credentials: `aws configure` (or SSO). Then `scripts/smoke_live.py`.
4. Deploy: `cd infra && sam build && sam deploy --guided` (needs AWS SAM CLI). Note the `ApiUrl` output.
5. Frontend: `cd frontend && VITE_API_URL=<ApiUrl> npm run build`, host `dist/` with Amplify Hosting (or any static host).
6. Scheduler: per-project one-time schedules that invoke `WakeFunction` (role ARN is a stack output). Not created automatically in this build; in the demo the time machine calls the same logic.
7. SES: new accounts are in sandbox (verified recipients only). Not wired: this build has no send function by design.
8. Agent Lambda (live mode in the cloud) is NOT in the template yet: package `backend/` with `requirements-agents.txt` (large; consider a container image or layer) as a separate function.
