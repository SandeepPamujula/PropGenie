# PropGenie Operations — Rollback Procedure

This document outlines the procedure to roll back deployments to the production (or development) environments in the event of an outage, regression, or critical failure.

---

## 1. Primary Rollback Method (GitHub Actions)

The safest and most auditable way to roll back is to re-run the manual **Production Deployment Pipeline** targeting a last-known-good commit SHA. This ensures that the state of your infrastructure (Terraform), backend code (Lambda), and frontend static files (S3/CloudFront) remains synchronized.

### Step-by-Step Instructions:
1. **Identify the Last-Known-Good Commit**:
   - Go to your repository on GitHub.
   - Click on the **Commits** history or the **Releases** page.
   - Locate the commit SHA of the version that was running successfully prior to the regression.

2. **Trigger the Production Deploy Workflow**:
   - Go to the **Actions** tab in your GitHub repository.
   - In the left sidebar, click on the **Production Deployment Pipeline** workflow.
   - On the right side, click the **Run workflow** dropdown.
   - Under **Use workflow from**, enter or select the Git ref (branch name `main`, tag, or the specific 40-character stable commit SHA).
   - Click the green **Run workflow** button.

3. **Approve the Environment Gate**:
   - Since the production workflow is bound to the `prod` environment, it will pause and request review.
   - An authorized reviewer must approve the deployment to proceed.

4. **Verify the Rollback**:
   - Monitor the workflow execution.
   - Ensure the **Smoke Test** step completes successfully and returns `200 OK` from the health check endpoint.
   - Check the custom monitoring alarms on AWS CloudWatch to ensure error rates return to normal.

---

## 2. Emergency CLI Rollback Method (Direct AWS)

If GitHub Actions is experiencing an outage and you need to restore service immediately, you can roll back the frontend assets and backend Lambda function directly using the AWS CLI.

### Prerequisites:
- AWS CLI installed and configured locally with administrator/deployment permissions.
- Local copy of the repository checked out at the last-known-good commit.

### Step 1: Rollback Backend Lambda Function
1. Clean check out the stable commit locally:
   ```bash
   git checkout <stable-commit-sha>
   ```
2. Navigate to the backend directory and re-package the stable code:
   ```bash
   cd backend
   mkdir -p dist
   pip install -r requirements.txt --platform manylinux2014_x86_64 --only-binary=:all: -t dist/
   cp -r agents db models observability portal_configs utils graph.py handler.py dist/
   cd dist
   zip -r ../lambda_rollback.zip .
   cd ..
   ```
3. Update the production Lambda function code:
   ```bash
   aws lambda update-function-code --function-name propgenie-agent-prod --zip-file fileb://lambda_rollback.zip
   ```
4. Verify the backend health:
   ```bash
   curl -f https://<prod-domain>/api/health
   ```

### Step 2: Rollback Frontend Assets
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Rebuild the frontend static files from the stable commit:
   ```bash
   npm install
   npm run build
   ```
3. Sync the stable files to S3:
   ```bash
   # Retrieve the bucket name and CloudFront distribution ID from Terraform outputs
   cd ../infra
   terraform init
   terraform workspace select prod
   S3_BUCKET=$(terraform output -raw s3_bucket_name)
   CLOUDFRONT_DIST_ID=$(terraform output -raw distribution_id)
   
   # Sync assets
   cd ../frontend
   aws s3 sync out/ s3://$S3_BUCKET/ --delete
   ```
4. Invalidate the CloudFront cache:
   ```bash
   aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DIST_ID --paths "/*"
   ```

---

## 3. Post-Rollback Auditing
After the rollback is complete and service is restored:
1. Document the incident and root cause.
2. If a hotfix is required, create a new branch from `main`, apply the fix, test it, and merge to `main`. Do **not** commit directly to the rolled-back state on GitHub.
3. Trigger a fresh deployment of the new fixed version to dev, verify, and manually trigger prod when ready.
