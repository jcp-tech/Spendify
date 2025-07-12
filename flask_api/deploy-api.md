# 🚀 GCP Cloud Run Deployment Guide – Flask API (`spendify-main`)

**Using Dockerfile.api (not default Dockerfile)**

---

## 1️⃣ Set Active GCP Project

```bash
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

---

## 2️⃣ Enable Required Services

```bash
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com
```

---

## 3️⃣ Build & Push Docker Image (using Dockerfile.api)
<!-- NOTE: If your using a Dockerfile.api then you need a YML file also. -->
```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME .
```

---

## 4️⃣ Deploy to Cloud Run (Flask, port 5000)

```bash
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME \
  --platform managed \
  --region $GOOGLE_CLOUD_LOCATION \
  --allow-unauthenticated \
  --memory 1Gi \
  --port 5000
```

---

## 5️⃣ Check Logs (optional)

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --project=$GOOGLE_CLOUD_PROJECT \
  --limit=50 \
  --freshness=1h \
  --format="value(textPayload)"
```

---

## 6️⃣ (Optional) Delete Old Service/Image

```bash
gcloud run services delete $SERVICE_NAME --region=$GOOGLE_CLOUD_LOCATION

gcloud container images delete gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME --quiet
```

---

## 📝 Summary Table

| Step            | Command                                                                                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Build Image** | `gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME .`                                                                                               |
| **Deploy**      | `gcloud run deploy $SERVICE_NAME --image gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME --platform managed --region $GOOGLE_CLOUD_LOCATION --allow-unauthenticated --memory 1Gi --port 5000`         |
| **View Logs**   | `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" --project=$GOOGLE_CLOUD_PROJECT --limit=50 --freshness=1h --format="value(textPayload)"`  |
| **Delete**      | `gcloud run services delete $SERVICE_NAME --region=$GOOGLE_CLOUD_LOCATION`<br>`gcloud container images delete gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME --quiet`                                 |

---

**Cloud Run will give you a public URL after deployment, e.g.:**
`https://spendify-main-xxxxx.a.run.app`