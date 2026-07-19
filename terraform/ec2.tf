# ec2.tf
# The actual virtual machine that will run k3s, provisioned by
# Ansible (Milestone 11), then hosting the containerized app via
# Kubernetes/Helm (Milestone 12).

# Automatically finds the latest official Ubuntu 22.04 AMI, rather
# than hardcoding an AMI ID (which is region-specific and changes
# over time as Canonical releases updates).
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical's official AWS account

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Generates an SSH key pair locally via Terraform, rather than
# manually creating one in the AWS console — keeps the whole setup
# reproducible from code.
resource "tls_private_key" "sentinel_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "sentinel_key_pair" {
  key_name   = "sentinel-key"
  public_key = tls_private_key.sentinel_key.public_key_openssh
}

# Saves the private key locally so you can actually use it to SSH in.
# This file must never be committed — already covered by .gitignore,
# but worth being explicit about here too.
resource "local_file" "sentinel_private_key" {
  content         = tls_private_key.sentinel_key.private_key_pem
  filename        = "${path.module}/sentinel-key.pem"
  file_permission = "0400"   # SSH requires strict permissions on private keys
}

resource "aws_instance" "sentinel_ec2" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.medium"
  subnet_id              = aws_subnet.sentinel_public_subnet.id
  vpc_security_group_ids = [aws_security_group.sentinel_sg.id]
  key_name               = aws_key_pair.sentinel_key_pair.key_name

  root_block_device {
    volume_size = 30   # GB — enough for the OS, Docker images, k3s
    volume_type = "gp3"
  }

  tags = {
    Name = "sentinel-ec2"
  }
}

# Prints the instance's public IP after apply, so you don't have to
# dig through the AWS console to find it.
output "instance_public_ip" {
  value = aws_instance.sentinel_ec2.public_ip
}


resource "aws_eip" "sentinel_eip" {
  instance = aws_instance.sentinel_ec2.id
  domain   = "vpc"

  tags = {
    Name = "sentinel-eip"
  }
}
output "elastic_ip" {
  value = aws_eip.sentinel_eip.public_ip
}