#!/usr/bin/env bash
# Provisiona a cadeia de credencial da app:
#   key JSON -> Secret Manager, SA de bootstrap da VM, systemd via FINANCAS_SA_SECRET.
#
# Idempotente: pode ser reexecutado para rotacionar a key (adiciona nova versão).
#
# Uso: provision_credential.sh /caminho/para/financas-sa.json
set -euo pipefail

PROJECT="${PROJECT:-free-project-508015}"
ZONE="${ZONE:-us-central1-a}"
INSTANCE="${INSTANCE:-financial-instance}"
VM_SA_NAME="${VM_SA_NAME:-financas-vm}"
SECRET="${SECRET:-financas-sa-key}"
KEY_FILE="${1:?uso: provision_credential.sh <caminho do json da SA>}"

VM_SA="$VM_SA_NAME@$PROJECT.iam.gserviceaccount.com"
SECRET_NAME="projects/$PROJECT/secrets/$SECRET/versions/latest"

echo "==> habilitando Secret Manager API"
gcloud services enable secretmanager.googleapis.com --project "$PROJECT" --quiet

echo "==> criando secret (se nao existir)"
if ! gcloud secrets describe "$SECRET" --project "$PROJECT" --quiet >/dev/null 2>&1; then
  gcloud secrets create "$SECRET" --project "$PROJECT" --replication-policy=automatic
fi
VERSION=$(gcloud secrets versions add "$SECRET" --project "$PROJECT" --data-file="$KEY_FILE")
echo "    ok, versao $VERSION"

echo "==> criando SA de bootstrap da VM"
if ! gcloud iam service-accounts describe "$VM_SA" --project "$PROJECT" --quiet >/dev/null 2>&1; then
  gcloud iam service-accounts create "$VM_SA_NAME" --project "$PROJECT" --display-name="financas VM bootstrap"
fi

echo "==> IAM: SA da VM pode ler o secret"
gcloud secrets add-iam-policy-binding "$SECRET" --project "$PROJECT" \
  --member "serviceAccount:$VM_SA" --role roles/secretmanager.secretAccessor \
  --quiet >/dev/null 2>&1 || true
gcloud secrets add-iam-policy-binding "$SECRET" --project "$PROJECT" \
  --member "serviceAccount:$VM_SA" --role roles/secretmanager.secretVersionAdder \
  --quiet >/dev/null 2>&1 || true

echo "==> anexando SA de bootstrap a instancia"
CURRENT_SA=$(gcloud compute instances describe "$INSTANCE" --zone "$ZONE" \
  --format="value(serviceAccounts[].email)" 2>/dev/null || true)
if [[ "$CURRENT_SA" != "$VM_SA" ]]; then
  gcloud compute instances stop "$INSTANCE" --zone "$ZONE" --quiet
  gcloud compute instances set-service-account "$INSTANCE" --zone "$ZONE" \
    --service-account "$VM_SA" --scopes cloud-platform
  gcloud compute instances start "$INSTANCE" --zone "$ZONE" --quiet
else
  echo "    SA ja anexada, sem stop/start"
fi

echo "==> aplicando systemd unit (FINANCAS_SA_SECRET = $SECRET_NAME)"
gcloud compute ssh "$INSTANCE" --zone "$ZONE" --command "
  sudo sed -i '/^Environment=/d' /etc/systemd/system/financas.service &&
  sudo sed -i '/^\[Service\]/a Environment=FINANCAS_SA_SECRET=$SECRET_NAME' /etc/systemd/system/financas.service &&
  sudo systemctl daemon-reload" --quiet

echo "pronto. remova a key antiga do disco e reinicie o servico:"
echo "  gcloud compute ssh $INSTANCE --zone $ZONE -- 'sudo rm /home/Johnny/financas-app/secrets/financas-sa.json && sudo systemctl restart financas'"