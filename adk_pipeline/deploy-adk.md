0. **Set Active GCP Project:**

```bash
gcloud config set project $GOOGLE_CLOUD_PROJECT
```
<!-- gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT -->


1. **Run this command:**

   ```sh
   gcloud auth application-default login
   ```

   * This will open a browser window. Log in with your Google account that has permissions for your project.

2. **Confirm it worked:**

   ```sh
   gcloud auth application-default print-access-token
   ```

   * You should see a long access token (not an error).


3.  **Deploy with**
<!-- 
> Template
```sh
adk deploy agent_engine --project=[project] --region=[region] --staging_bucket=[staging_bucket] --display_name=[app_name] path/to/my_agent
```
> Filled
```sh
adk deploy agent_engine --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --staging_bucket=$STAGING_BUCKET --display_name=spendify-adk ./receipt_classifier
```
-->
> Template
```sh
adk deploy cloud_run \
  --project=<YOUR_GCP_PROJECT_ID> \
  --region=<YOUR_GCP_REGION> \
  --service_name=<SERVICE_NAME> \
  --app_name=<APP_NAME> \
  --port=8080 \
  --log_level=info \
  --with_ui \
  ./path/to/your_agent
```

> Filled
```sh
adk deploy cloud_run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --service_name=$SERVICE_NAME \
  --app_name=$SERVICE_NAME \
  --port=8080 \
  --log_level=info \
  --with_ui \
  ./receipt_classifier
```

---