resource "aws_cloudfront_distribution" "backend" {
  origin {
    domain_name = "${aws_api_gateway_rest_api.api.id}.execute-api.${var.aws_region}.amazonaws.com"
    origin_path = "/${var.stage}"
    origin_id   = "api"
  }
  
  default_cache_behavior {
    target_origin_id = "api"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods       = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods        = ["GET", "HEAD"]
    min_ttl               = 0
    default_ttl           = 3600
    max_ttl               = 86400
    forwarded_values {
      query_string = false
      headers      = ["*"]
      cookies {
        forward = "all"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  enabled             = true
  is_ipv6_enabled     = true
}

output "cloudfront_domain" {
  value = "https://${aws_cloudfront_distribution.backend.domain_name}"
}
