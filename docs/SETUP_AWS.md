# AWS setup and deployment

## Current deployment (9 October 2026)

| | |
|---|---|
| Site (Amplify Hosting) | https://main.d2vnrqt0vyz925.amplifyapp.com (app `d2vnrqt0vyz925`, branch `main`) |
| API | https://f9x2xp42wg.execute-api.ap-south-1.amazonaws.com |
| Stack | `solarsabha` in ap-south-1, `ReaderMode=offline`, `AllowedOrigin` = the site |

On Windows build with `sam build --use-container` (Docker Desktop running): a plain Windows build pulls a Windows-only
dependency of the MCP library. To redeploy the site: build `frontend/` with `VITE_API_URL=<ApiUrl>`, zip `dist/`, then
`aws amplify create-deployment`, upload the zip, `aws amplify start-deployment` (or connect the GitHub repo in the Amplify console).
To remove everything: `sam delete --stack-name solarsabha` and `aws amplify delete-app --app-id d2vnrqt0vyz925`.

## 1. Account and access
1. Verify your student profile on AWS Builder Center (event requirement). A Builder ID is not an AWS account.
2. Create an AWS account, turn on MFA for the root user, and create a **Zero spend** budget (Billing > Budgets).
3. Create an IAM user for the CLI (or use IAM Identity Center), create a CLI access key, and run `aws configure`
   with region `ap-south-1`. Check with `aws sts get-caller-identity`. Never paste keys into chat or commit them.
4. Install the AWS CLI and the SAM CLI (`winget install Amazon.AWSCLI` and `winget install Amazon.SAM-CLI` on Windows).

## 2. Bedrock (only for the live AI Reader)
1. In the Bedrock console (Mumbai, ap-south-1), open a Claude model in the playground and send one message. Submit
   Anthropic's one-time use-case form if it appears.
2. Find the inference profile id: `aws bedrock list-inference-profiles --region ap-south-1`. We use the India-only profile
   `in.anthropic.claude-sonnet-5` (data stays in India); `in.anthropic.claude-haiku-4-5-20251001-v1:0` is the cheaper fallback.
3. Put it in `.env` as `BEDROCK_MODEL_ID=...` and test: `python scripts/smoke_live.py`, then `python scripts/run_evals.py --mode live`.

**New accounts:** a brand-new account on the AWS **Free plan** may get `ValidationException: Operation not allowed` for every
Bedrock model (we saw this for Claude, Nova and Mistral). Upgrading to the paid plan (credits still apply first) or an AWS
Support case lifts it. Until then, use the offline reader (`READER_MODE=offline`, the default); everything else works.

## 3. Deploy the backend
```bash
cd infra
sam build
sam deploy --guided      # stack name e.g. solarsabha, region ap-south-1
```
Parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `ReaderMode` | `offline` | `live` uses the Bedrock Reader agent |
| `BedrockModelId` | empty | inference profile id for live mode |
| `AllowedOrigin` | `*` | set to your site's origin (e.g. the Amplify URL) for production |
| `RetentionDays` | `365` | projects and files are deleted automatically after this |

It creates: the HTTP API (throttled), the API and wake-up Lambdas, a DynamoDB table (TTL, point-in-time recovery,
encryption), a private encrypted S3 bucket (TLS only, lifecycle expiry), the EventBridge Scheduler role, and 30-day log groups.
Note the `ApiUrl` output.

## 4. Host the frontend (Amplify Hosting)
```bash
cd frontend
VITE_API_URL=<ApiUrl> VITE_PRIVACY_CONTACT="<your contact>" npm run build
```
Upload `frontend/dist/` with Amplify Hosting (manual deploy, or connect the GitHub repo with build command
`npm ci && npm run build`, base directory `frontend`, output `dist`, and the two `VITE_` variables). Then redeploy the
backend with `AllowedOrigin` set to the Amplify URL.

## 5. How the alarms work
After every change the API sets a one-time EventBridge schedule `solarsabha-<project id>` for the day the active stage is
due (or a week later if it is already late). It invokes the wake-up Lambda, which recomputes the project, logs what the
Chaser found, and sets the next alarm. Deleting a project removes its schedule. Code: `backend/solarsabha/alarm.py`.

## 6. Deliberately not used
- **SES / sending**: the product never sends anything; letters are downloaded and sent by a person.
- **Step Functions**: approvals are stored state and waiting is done by the scheduler, so no long-running workflow is needed.
- **Cognito**: access is per-project keys with roles. Add Cognito in front of the API if you need verified identities.
