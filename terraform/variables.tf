variable "environment" {
  type    = string
  default = "dev"
}

variable "app_image" {
  type    = string
  default = "taskflow:1.0"
}

variable "external_port" {
  type    = number
  default = 8090
}

variable "memory_mb" {
  type    = number
  default = 256
}