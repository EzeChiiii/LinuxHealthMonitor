# vpc.tf
# The network foundation everything else lives inside. A single VPC
# with one public subnet — appropriate for a single EC2 instance
# running k3s. A more complex production setup might split public/
# private subnets across multiple availability zones, but that's
# unnecessary complexity for this scope.

resource "aws_vpc" "sentinel_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "sentinel-vpc"
  }
}

# A public subnet — "public" because we'll attach an internet gateway
# and route table below that let resources here reach (and be reached
# from) the internet, which the EC2 instance needs for SSH access and
# for the API/frontend to be publicly reachable.
resource "aws_subnet" "sentinel_public_subnet" {
  vpc_id                  = aws_vpc.sentinel_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"

  tags = {
    Name = "sentinel-public-subnet"
  }
}

# Internet gateway — the actual door between the VPC and the internet.
# Without this, nothing inside the VPC can reach or be reached from
# outside, regardless of subnet configuration.
resource "aws_internet_gateway" "sentinel_igw" {
  vpc_id = aws_vpc.sentinel_vpc.id

  tags = {
    Name = "sentinel-igw"
  }
}

# Route table directing internet-bound traffic (0.0.0.0/0) out through
# the internet gateway, then associates that route table with our
# public subnet — this is what actually makes the subnet "public."
resource "aws_route_table" "sentinel_public_rt" {
  vpc_id = aws_vpc.sentinel_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.sentinel_igw.id
  }

  tags = {
    Name = "sentinel-public-rt"
  }
}

resource "aws_route_table_association" "sentinel_public_rta" {
  subnet_id      = aws_subnet.sentinel_public_subnet.id
  route_table_id = aws_route_table.sentinel_public_rt.id
}