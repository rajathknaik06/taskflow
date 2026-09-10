output "app_url" {
  value = "http://localhost:${var.external_port}"
}

output "container_name" {
  value = docker_container.app_server.name
}