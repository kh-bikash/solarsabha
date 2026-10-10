# AWS setup and deployment

## Current deployment (10 October 2026)

| | |
|---|---|
| Site (Amplify Hosting) | https://solarsabha.d2vnrqt0vyz925.amplifyapp.com (app `SolarSabha`, id `d2vnrqt0vyz925`, branch `solarsabha`) |
| API | https://f9x2xp42wg.execute-api.ap-south-1.amazonaws.com |
| Stack | `solarsabha` in ap-south-1, `ReaderMode=live`, `ModelProvider=gemini`, `AllowedOrigin` = the site |
| Model keys | SSM SecureString parameters under `/solarsabha/` |

On Windows build with `sam build --use-container` (Docker Desktop running): a plain Windows build pulls a Windows-only
dependency of the MCP library. To redeploy the site: build `frontend/` with `VITE_API_URL=<ApiUrl>`, zip `dist/`, then
`aws amplify create-deployment --app-id d2vnrqt0vyz925 --branch-name solarsabha`, upload the zip to the returned URL,
`aws amplify start-deployment` (or connect the GitHub repo in the Amplify console).
To remove everything: `sam delete --stack-name solarsabha` and `aws amplify delete-app --app-id d2vnrqt0vyz925`.

## 1. Account and access
1. Verify your student profile on AWS Builder Center (event requirement). A Builder ID is not an AWS account.
2. Create an AWS account, turn on MFA for the root user, and create a **Zero spend** budget (Billing > Budgets).
3. Create an IAM user for the CLI (or use IAM Identity Center), create a CLI access key, and run `aws configure`
   with region `ap-south-1`. Check with `aws sts get-caller-identity`. Never paste keys into chat or commit them.
4. Install the AWS CLI and the SAM CLI (`winget install Amazon.AWSCLI` and `winget install Amazon.SAM-CLI` on Windows).

## 2. The model (only for the live agents)
The agents run on **Gemini** by default. Keys are stored encrypted in SSM Parameter Store and read by the Lambda at run
time; they never appear in the template, the environment variables or the code.

1. Create a Gemini API key in Google AI Studio and store it:
   ```bash
   aws ssm put-parameter --region ap-south-1 --type SecureString --name /solarsabha/gemini-api-key --value "<key>"
   ```
2. Optional text-only backup, used for the review, DISCOM replies and polishing when every Gemini model is out of quota
   (documents are never sent to them):
   ```bash
   aws ssm put-parameter --region ap-south-1 --type SecureString --name /solarsabha/bazaarlink-api-key --value "<key>"
   ```
3. Locally, put the same keys in `.env` (`GEMINI_API_KEY`, `BAZAARLINK_API_KEY`, `READER_MODE=live`) and
   test: `python scripts/smoke_live.py`, then `python scripts/run_evals.py --mode live`.

The Gemini free tier allows about 20 requests per model per day, which a single review can use up. For judging or real
use, turn on billing for the key (it also stops Google using the content to improve its products; see the privacy notice).

**Amazon Bedrock instead:** deploy with `ModelProvider=bedrock` and `BedrockModelId` set to an inference profile, such as
the India-only `in.anthropic.claude-sonnet-5` (data stays in India). A brand-new account on the AWS **Free plan** may get
`ValidationException: Operation not allowed` for every Bedrock model; upgrading to the paid plan (credits still apply
first) or an AWS Support case lifts it.

## 3. Deploy the backend
```bash
cd infra
sam build --use-container
sam deploy --guided      # stack name solarsabha, region ap-south-1
```
Parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `ReaderMode` | `offline` | `live` switches on the agents; `offline` is the plain-rule reader with no AI |
| `ModelProvider` | `gemini` | `gemini` or `bedrock` |
| `GeminiModelChain` | 7 models | Gemini models in fallback order |
| `GeminiKeyParam` | `/solarsabha/gemini-api-key` | SSM parameter with the Gemini key |
| `BazaarlinkKeyParam` | empty (off) | SSM parameter with the backup key, e.g. `/solarsabha/bazaarlink-api-key` |
| `BedrockModelId` | empty | inference profile id when `ModelProvider=bedrock` |
| `AllowedOrigin` | `*` | set to your site's origin (the Amplify URL) for production |
| `RetentionDays` | `365` | projects and files are deleted automatically after this |

It creates: the HTTP API (throttled), the API and wake-up Lambdas, a DynamoDB table (TTL, point-in-time recovery,
encryption, conditional writes for optimistic locking), a private encrypted S3 bucket (TLS only, lifecycle expiry), the
EventBridge Scheduler role, and 30-day log groups. The API Lambda may read only `/solarsabha/*` parameters and invoke
only itself (to run the agents' review in the background, past API Gateway's 30-second limit). Note the `ApiUrl` output.

## 4. Host the frontend (Amplify Hosting)
```bash
cd frontend
VITE_API_URL=<ApiUrl> VITE_PRIVACY_CONTACT="<your contact>" npm run build
```
Upload `frontend/dist/` with Amplify Hosting (manual deploy, or connect the GitHub repo with build command
`npm ci && npm run build`, base directory `frontend`, output `dist`, and the two `VITE_` variables). Name the branch
after the product (ours is `solarsabha`) so the URL reads `https://solarsabha.<app id>.amplifyapp.com`. Then redeploy
the backend with `AllowedOrigin` set to that URL.

## 5. How the alarms work
After every change the API sets a one-time EventBridge schedule `solarsabha-<project id>` for the day the active stage is
due (or a week later if it is already late). It invokes the wake-up Lambda, which recomputes the project, logs what the
Chaser found, and sets the next alarm. Deleting a project removes its schedule. Code: `backend/solarsabha/alarm.py`.

## 6. Deliberately not used
- **SES / sending**: the product never sends anything; letters are downloaded and sent by a person.
- **Step Functions**: approvals are stored state and waiting is done by the scheduler, so no long-running workflow is needed.
  The one long task (the agents' review) runs as an asynchronous self-invocation of the API Lambda.
- **Secrets Manager**: SSM SecureString holds the model keys at no cost; rotate by overwriting the parameter.
- **Cognito**: access is per-project keys with roles. Add Cognito in front of the API if you need verified identities.
