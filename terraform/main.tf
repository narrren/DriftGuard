terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "random_id" "bucket_suffix" {
  byte_length = 8
}

locals {
  # Calculate expiry time: Now + 24 hours (example logic, usually passed via var or calculated externally if possible, 
  # but terraform's time_offset resource is better. strictly sticking to SRD 'Inject a tag').
  # For simplicity in this static file, we will require the tag to be passed in or default to a placeholder.
  # Real implementation would use an input variable for the timestamp.
}

# Variable moved to variables.tf

resource "aws_s3_bucket" "ephemeral_env" {
  bucket = "driftguard-env-${random_id.bucket_suffix.hex}"

  tags = {
    Name                 = "DriftGuard Ephemeral"
    driftguard_ttl_expiry = var.ttl_expiry
    Environment          = "Preview"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.ephemeral_env.bucket
}
