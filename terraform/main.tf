terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "taskflow_net" {
  name = "taskflow-${var.environment}"
}

resource "docker_container" "app_server" {
  name  = "taskflow-${var.environment}"
  image = var.app_image

  networks_advanced {
    name = docker_network.taskflow_net.name
  }

  ports {
    internal = 5000
    external = var.external_port
  }

  memory = var.memory_mb
}