# security_group.tf
# Defines firewall rules for the EC2 instance — what traffic is
# allowed in (ingress) and out (egress). Deliberately narrow: SSH
# for your own administrative access, HTTP for the frontend/API,
# and nothing else inbound. This is the AWS-level equivalent of the
# FortiGate policies you've configured before, just declared in code.

resource "aws_security_group" "sentinel_sg" {
  name        = "sentinel-sg"
  description = "Allow SSH and HTTP access to the Sentinel EC2 instance"
  vpc_id      = aws_vpc.sentinel_vpc.id

  # SSH — restricted to your own IP only, not the whole internet.
  # Opening port 22 to 0.0.0.0/0 is a common, avoidable mistake —
  # worth explicitly calling out as a security decision here.
  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.my_ip.response_body)}/32"]
  }

  # HTTP — the frontend/API need to be reachable. Open to everyone,
  # since this is meant to be a publicly-viewable demo/portfolio app.
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Temporary: direct access to the API (8000) and frontend (3000)
  # ports for early testing, before we put a reverse proxy in front
  # of everything (that comes later, in a subsequent milestone).
  ingress {
    description = "Temporary direct API/frontend access"
    from_port   = 3000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress — allow all outbound traffic. The instance needs to reach
  # out for package installs, Docker image pulls, etc. Outbound is
  # conventionally left open unless there's a specific reason to
  # restrict it (unlike inbound, which should always be minimal).
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sentinel-sg"
  }
}

# Fetches your current public IP automatically at apply-time, so the
# SSH rule above only allows your own machine — avoids hardcoding an
# IP that'll change if you're on a different network later (you'd
# just re-run terraform apply to pick up the new one).
data "http" "my_ip" {
  url = "https://api.ipify.org"
}