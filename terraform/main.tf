# main.tf
# Declares Terraform itself and the AWS provider — this tells
# Terraform "we're managing AWS resources," and which region to
# create them in by default. Nothing here creates any actual
# infrastructure yet — this is just the foundational setup every
# resource block later will build on.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"   # change if you configured a different region earlier
}