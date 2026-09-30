data "aws_iam_policy_document" "assume_ec2" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = "${var.name}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
  tags               = var.tags
}

# Lets you connect with SSM Session Manager instead of opening SSH
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "cloudwatch" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

data "aws_iam_policy_document" "s3_access" {
  count = length(var.s3_bucket_arns) > 0 ? 1 : 0

  statement {
    actions   = ["s3:ListBucket"]
    resources = var.s3_bucket_arns
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = [for arn in var.s3_bucket_arns : "${arn}/*"]
  }
}

resource "aws_iam_role_policy" "s3_access" {
  count  = length(var.s3_bucket_arns) > 0 ? 1 : 0
  name   = "${var.name}-s3-access"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.s3_access[0].json
}

resource "aws_iam_instance_profile" "this" {
  name = "${var.name}-ec2-profile"
  role = aws_iam_role.this.name
}
