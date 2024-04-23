resource "aws_ecr_repository" "app_ecr_repo" {
  name = "app-repo"
}

resource "terraform_data" "docker_packaging" {
  triggers = {
    "run_at" = timestamp()
    files = "${filebase64sha256("../Dockerfile")}"
  }
  provisioner "local-exec" {
    command = <<EOF
aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app_ecr_repo.repository_url}
docker build -t ${aws_ecr_repository.app_ecr_repo.repository_url}:latest ..
docker push ${aws_ecr_repository.app_ecr_repo.repository_url}:latest
EOF
  }
}

