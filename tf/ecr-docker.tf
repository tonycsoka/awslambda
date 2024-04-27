resource "aws_ecr_repository" "backend" {
  name = "backend"
}

resource "terraform_data" "docker" {
  triggers_replace = {
    hash = md5(join("-", [for x in fileset("", "../{*.py,*.txt,Dockerfile}") : filemd5(x)]))
  }
  provisioner "local-exec" {
    command = <<EOF
aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.backend.repository_url}
docker build -t ${aws_ecr_repository.backend.repository_url}:latest ..
docker push ${aws_ecr_repository.backend.repository_url}:latest
EOF
  }
}

data "aws_ecr_image" "latest" {
  repository_name = aws_ecr_repository.backend.name
  image_tag       = "latest"
  depends_on      = [terraform_data.docker]
}

