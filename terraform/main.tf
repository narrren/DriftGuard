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

  # REMOTE BACKEND (State Locking)
  # Ensure you create this bucket and table manually before running!
  backend "s3" {
    bucket         = "driftguard-terraform-state-LOCK" # @TODO: Replace with unique bucket
    key            = "global/s3/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "driftguard-terraform-locks"      # @TODO: Replace with DynamoDB table
    encrypt        = true
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
