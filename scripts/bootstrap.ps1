<#
.SYNOPSIS
  One-time AWS bootstrap for crapsim - the resources Terraform cannot create
  for itself (its own state bucket, and the roles CI assumes to run it).

.DESCRIPTION
  Adapted from mbroadfo/spa-on-aws's bootstrap with the compute half swapped:
  this app is a stateful SSE server on ECS Fargate, not Lambda + API Gateway,
  and it serves its own SPA - so there is no assets bucket, no CloudFront and
  no ACM here.

  Creates:
    1. S3 state bucket  {app}-tf-state   (versioned, encrypted, access blocked)
    2. GitHub OIDC provider              (shared per account; reused if present)
    3. IAM role  {app}-terraform         (runs terraform apply from CI)
    4. IAM role  {app}-ci                (builds/pushes images, updates ECS)
    5. GitHub Actions variables + secrets

  Idempotent: existing resources are updated in place, never recreated.

  Networking note: Terraform uses the account's DEFAULT VPC rather than
  creating one. Fargate needs a public subnet only for egress (the ECR pull
  and the outbound Cloudflare tunnel) with no inbound rules at all, so
  building a VPC would add IAM surface and an internet gateway for no
  benefit. Hence the terraform role gets ec2:Describe* plus security-group
  actions, but no VPC/subnet creation rights.

  Requires a credential that can manage IAM. The `terraform` profile is
  deliberately not enough - it has no IAM permissions.

  This file is deliberately pure ASCII with CRLF endings: Windows PowerShell
  5.1 reads .ps1 as ANSI unless there is a BOM, so a stray UTF-8 character
  (an em dash, say) corrupts string parsing several lines later. Enforced by
  .gitattributes.

.EXAMPLE
  ./scripts/bootstrap.ps1 -CfZoneId <zone-id> -CfToken <token>

.EXAMPLE
  # Also trust a feature branch while the pipeline is being built out
  ./scripts/bootstrap.ps1 -CfZoneId <id> -CfToken <tok> -Branch master,right-side-panel
#>
[CmdletBinding()]
param(
  [string]$App = "crapsim",
  [string]$Environment = "prod",
  [string]$Domain = "crapsim.xaminisalamini.com",
  [string]$GithubRepo = "mbroadfo/craps_simulator",
  [string[]]$Branch = @("master"),
  [string]$Region = "us-west-2",
  [string]$Profile = "admin",
  [Parameter(Mandatory = $true)][string]$CfZoneId,
  [Parameter(Mandatory = $true)][string]$CfAccountId,
  # Optional so the AWS half can be bootstrapped before a token exists.
  # Re-run with -CfToken later to set the secret; the script is idempotent.
  [string]$CfToken = "",
  # An IAM principal additionally allowed to assume these roles directly, so
  # Terraform can be run locally without an admin key. Empty means CI-only.
  [string]$LocalOperatorArn = ""
)

# Deliberately NOT "Stop": aws and gh write ordinary diagnostics to stderr,
# and under EAP=Stop, PowerShell 5.1 turns that into a terminating
# NativeCommandError before $LASTEXITCODE can be inspected - which buries the
# real message. Exit codes are checked explicitly instead, via Invoke-Native
# and Assert-Ok below.
$ErrorActionPreference = "Continue"

# powershell.exe -File passes "a,b" as ONE string rather than binding it as an
# array, which silently produced a single bogus subject
# (...:ref:refs/heads/master,right-side-panel) matching no branch at all.
# Normalize either invocation form into a real list.
$Branch = @($Branch | ForEach-Object { $_ -split ',' } | Where-Object { $_.Trim() } | ForEach-Object { $_.Trim() })

$env:AWS_PROFILE = $Profile
$env:AWS_DEFAULT_REGION = $Region

$StateBucket   = "$App-tf-state"
$TfRole        = "$App-terraform"
$CiRole        = "$App-ci"
$SsmSecretPath = "/$App/$Environment/secrets"
$tmp = New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP "crapsim-bootstrap")

function Write-Step($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok($m)   { Write-Host "  [ok]   $m" -ForegroundColor Green }
function Write-Skip($m) { Write-Host "  [skip] $m" -ForegroundColor DarkGray }

# Runs a native command, returns its combined output as a string, and leaves
# $LASTEXITCODE (which is global) for the caller to check.
function Invoke-Native {
  param([Parameter(Mandatory = $true)][scriptblock]$Command)
  $output = & $Command 2>&1
  return ($output | Out-String)
}

function Assert-Ok {
  param([string]$What, [string]$Output)
  if ($LASTEXITCODE -ne 0) {
    throw "$What failed (exit $LASTEXITCODE):`n$Output"
  }
}

# --------------------------------------------------------------- preflight
Write-Step "Preflight"
$identityJson = Invoke-Native { aws sts get-caller-identity --output json }
if ($LASTEXITCODE -ne 0) {
  throw "Profile '$Profile' has no usable credentials. Rotate its access key in IAM and update ~/.aws/credentials.`n$identityJson"
}
$identity = $identityJson | ConvertFrom-Json
$AccountId = $identity.Account
Write-Ok "account $AccountId as $($identity.Arn)"

$null = Invoke-Native { aws iam list-open-id-connect-providers --output json }
if ($LASTEXITCODE -ne 0) {
  throw "Credential '$Profile' cannot perform IAM actions, which bootstrap requires. Use an admin credential."
}
Write-Ok "IAM access confirmed"

$null = Invoke-Native { gh auth status }
if ($LASTEXITCODE -ne 0) { throw "gh is not authenticated. Run: gh auth login" }
Write-Ok "gh authenticated"

# ------------------------------------------------------------ OIDC subject
# GitHub issues either the classic subject (repo:owner/repo:...) or an
# immutable one (repo:owner@ownerid/repo@repoid:...). Ask which this repo
# actually uses and trust both, so turning immutable subjects on later cannot
# silently lock CI out. Pinned to named branches: a fork's pull_request run
# carries a different ref and so cannot assume these roles - which matters
# here because this repo is public.
Write-Step "OIDC subject"
$subRaw = Invoke-Native { gh api "repos/$GithubRepo/actions/oidc/customization/sub" }
$prefixes = @("repo:$GithubRepo")
if ($LASTEXITCODE -eq 0) {
  $subInfo = $subRaw | ConvertFrom-Json
  if ($subInfo.sub_claim_prefix -and $subInfo.sub_claim_prefix -ne "repo:$GithubRepo") {
    $prefixes += $subInfo.sub_claim_prefix
  }
}
$RepoSubs = foreach ($p in $prefixes) { foreach ($b in $Branch) { "${p}:ref:refs/heads/${b}" } }
$RepoSubJson = ($RepoSubs | ForEach-Object { '"' + $_ + '"' }) -join ", "
foreach ($s in $RepoSubs) { Write-Ok "trusts $s" }

# ---------------------------------------------------------- 1. state bucket
Write-Step "1/5  Terraform state bucket: $StateBucket"
$null = Invoke-Native { aws s3api head-bucket --bucket $StateBucket }
if ($LASTEXITCODE -eq 0) {
  Write-Skip "bucket already exists"
} else {
  if ($Region -eq "us-east-1") {
    $o = Invoke-Native { aws s3api create-bucket --bucket $StateBucket }
  } else {
    $o = Invoke-Native { aws s3api create-bucket --bucket $StateBucket --create-bucket-configuration "LocationConstraint=$Region" }
  }
  Assert-Ok "create-bucket" $o
  Write-Ok "created"
}
$o = Invoke-Native { aws s3api put-bucket-versioning --bucket $StateBucket --versioning-configuration "Status=Enabled" }
Assert-Ok "put-bucket-versioning" $o
$o = Invoke-Native { aws s3api put-public-access-block --bucket $StateBucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" }
Assert-Ok "put-public-access-block" $o
# Written to a file: inline JSON with escaped quotes does not survive
# PowerShell -> aws-cli argument quoting reliably on Windows.
$encPath = Join-Path $tmp "encryption.json"
'{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' | Set-Content -Path $encPath -Encoding ascii
$o = Invoke-Native { aws s3api put-bucket-encryption --bucket $StateBucket --server-side-encryption-configuration "file://$encPath" }
Assert-Ok "put-bucket-encryption" $o
Write-Ok "versioned, AES256-encrypted, public access blocked"

# --------------------------------------------------------- 2. OIDC provider
Write-Step "2/5  GitHub OIDC provider"
$OidcArn = "arn:aws:iam::${AccountId}:oidc-provider/token.actions.githubusercontent.com"
$providersRaw = Invoke-Native { aws iam list-open-id-connect-providers --output json }
Assert-Ok "list-open-id-connect-providers" $providersRaw
$providers = $providersRaw | ConvertFrom-Json
if ($providers.OpenIDConnectProviderList.Arn -contains $OidcArn) {
  Write-Skip "provider already exists (shared per account)"
} else {
  $o = Invoke-Native { aws iam create-open-id-connect-provider --url "https://token.actions.githubusercontent.com" --client-id-list "sts.amazonaws.com" --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" }
  Assert-Ok "create-open-id-connect-provider" $o
  Write-Ok "created"
}

# A second statement, so a human (or this session) can assume the role with
# least privilege instead of keeping a long-lived admin key around. Note the
# roles' inline policies deliberately omit iam:UpdateAssumeRolePolicy, so a
# role cannot widen its own trust - changing it means re-running this script
# with admin credentials.
$localStatement = ""
if (-not [string]::IsNullOrWhiteSpace($LocalOperatorArn)) {
  $localStatement = @"
,
    {
      "Sid": "LocalOperator",
      "Effect": "Allow",
      "Principal": { "AWS": "$LocalOperatorArn" },
      "Action": "sts:AssumeRole"
    }
"@
}

$trustPath = Join-Path $tmp "trust.json"
@"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GitHubActionsOidc",
      "Effect": "Allow",
      "Principal": { "Federated": "$OidcArn" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
        "StringLike":   { "token.actions.githubusercontent.com:sub": [$RepoSubJson] }
      }
    }$localStatement
  ]
}
"@ | Set-Content -Path $trustPath -Encoding ascii

function Set-Role($name, $trustFile, $policyName, $policyFile) {
  $null = Invoke-Native { aws iam get-role --role-name $name }
  if ($LASTEXITCODE -eq 0) {
    $o = Invoke-Native { aws iam update-assume-role-policy --role-name $name --policy-document "file://$trustFile" }
    Assert-Ok "update-assume-role-policy $name" $o
    Write-Skip "$name exists, trust policy refreshed"
  } else {
    $o = Invoke-Native { aws iam create-role --role-name $name --assume-role-policy-document "file://$trustFile" }
    Assert-Ok "create-role $name" $o
    Write-Ok "$name created"
  }
  $o = Invoke-Native { aws iam put-role-policy --role-name $name --policy-name $policyName --policy-document "file://$policyFile" }
  Assert-Ok "put-role-policy $name" $o
  Write-Ok "$name inline policy applied"
}

# ------------------------------------------------------- 3. terraform role
Write-Step "3/5  IAM role: $TfRole"
$tfPolicyPath = Join-Path $tmp "tf-policy.json"
@"
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "TerraformState", "Effect": "Allow",
      "Action": ["s3:ListBucket","s3:GetBucketVersioning","s3:GetObject","s3:PutObject","s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::$StateBucket","arn:aws:s3:::$StateBucket/*"] },
    { "Sid": "EcrRepo", "Effect": "Allow", "Action": ["ecr:*"],
      "Resource": "arn:aws:ecr:${Region}:${AccountId}:repository/$App" },
    { "Sid": "EcrGlobal", "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken","ecr:DescribeRepositories","ecr:CreateRepository"],
      "Resource": "*" },
    { "Sid": "Ecs", "Effect": "Allow", "Action": ["ecs:*"], "Resource": "*" },
    { "Sid": "NetworkingReadAndSecurityGroups", "Effect": "Allow",
      "Action": ["ec2:Describe*","ec2:CreateSecurityGroup","ec2:DeleteSecurityGroup","ec2:AuthorizeSecurityGroupEgress","ec2:AuthorizeSecurityGroupIngress","ec2:RevokeSecurityGroupEgress","ec2:RevokeSecurityGroupIngress","ec2:CreateTags","ec2:DeleteTags"],
      "Resource": "*" },
    { "Sid": "AppScopedIam", "Effect": "Allow",
      "Action": ["iam:CreateRole","iam:DeleteRole","iam:GetRole","iam:PassRole","iam:TagRole","iam:UntagRole","iam:AttachRolePolicy","iam:DetachRolePolicy","iam:PutRolePolicy","iam:DeleteRolePolicy","iam:GetRolePolicy","iam:ListRolePolicies","iam:ListAttachedRolePolicies","iam:ListInstanceProfilesForRole","iam:CreateUser","iam:DeleteUser","iam:GetUser","iam:TagUser","iam:PutUserPolicy","iam:DeleteUserPolicy","iam:GetUserPolicy","iam:ListUserPolicies","iam:ListAccessKeys","iam:CreateAccessKey","iam:DeleteAccessKey"],
      "Resource": ["arn:aws:iam::${AccountId}:role/$App-*","arn:aws:iam::${AccountId}:user/$App-*"] },
    { "Sid": "Logs", "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:DeleteLogGroup","logs:DescribeLogGroups","logs:PutRetentionPolicy","logs:TagResource","logs:UntagResource","logs:ListTagsForResource"],
      "Resource": "*" },
    { "Sid": "Ssm", "Effect": "Allow",
      "Action": ["ssm:PutParameter","ssm:GetParameter","ssm:GetParameters","ssm:GetParameterHistory","ssm:DeleteParameter","ssm:AddTagsToResource","ssm:RemoveTagsFromResource","ssm:ListTagsForResource"],
      "Resource": "arn:aws:ssm:${Region}:${AccountId}:parameter$SsmSecretPath*" },
    { "Sid": "SsmList", "Effect": "Allow",
      "Action": ["ssm:DescribeParameters"],
      "Resource": "*" }
  ]
}
"@ | Set-Content -Path $tfPolicyPath -Encoding ascii
Set-Role $TfRole $trustPath "$TfRole-policy" $tfPolicyPath

# -------------------------------------------------------------- 4. ci role
Write-Step "4/5  IAM role: $CiRole"
$ciPolicyPath = Join-Path $tmp "ci-policy.json"
@"
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "EcrAuth", "Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*" },
    { "Sid": "EcrPush", "Effect": "Allow",
      "Action": ["ecr:BatchCheckLayerAvailability","ecr:CompleteLayerUpload","ecr:InitiateLayerUpload","ecr:PutImage","ecr:UploadLayerPart","ecr:BatchGetImage","ecr:GetDownloadUrlForLayer","ecr:DescribeImages"],
      "Resource": "arn:aws:ecr:${Region}:${AccountId}:repository/$App" },
    { "Sid": "EcsDeploy", "Effect": "Allow",
      "Action": ["ecs:RegisterTaskDefinition","ecs:DeregisterTaskDefinition","ecs:DescribeTaskDefinition","ecs:DescribeServices","ecs:UpdateService","ecs:ListServices","ecs:DescribeClusters"],
      "Resource": "*" },
    { "Sid": "PassTaskRoles", "Effect": "Allow", "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::${AccountId}:role/$App-*" },
    { "Sid": "SsmRead", "Effect": "Allow",
      "Action": ["ssm:GetParameter","ssm:GetParameters"],
      "Resource": "arn:aws:ssm:${Region}:${AccountId}:parameter$SsmSecretPath*" }
  ]
}
"@ | Set-Content -Path $ciPolicyPath -Encoding ascii
Set-Role $CiRole $trustPath "$CiRole-policy" $ciPolicyPath

# ----------------------------------------------- 5. GitHub vars and secrets
Write-Step "5/5  GitHub Actions variables and secrets"
$vars = [ordered]@{
  AWS_ACCOUNT_ID         = $AccountId
  AWS_REGION             = $Region
  TF_STATE_BUCKET        = $StateBucket
  TF_VAR_APP_NAME        = $App
  TF_VAR_ENVIRONMENT     = $Environment
  TF_VAR_CUSTOM_DOMAIN   = $Domain
  TF_VAR_SSM_SECRET_PATH = $SsmSecretPath
  CLOUDFLARE_ZONE_ID     = $CfZoneId
  CLOUDFLARE_ACCOUNT_ID  = $CfAccountId
}
foreach ($k in $vars.Keys) {
  $v = $vars[$k]
  $o = Invoke-Native { gh variable set $k --repo $GithubRepo --body $v }
  Assert-Ok "gh variable set $k" $o
  Write-Ok "variable $k"
}
if ([string]::IsNullOrWhiteSpace($CfToken)) {
  Write-Host "  [WARN] no -CfToken given; CLOUDFLARE_API_TOKEN not set." -ForegroundColor Yellow
  Write-Host "         Terraform cannot manage DNS/tunnel/Access until you re-run with -CfToken." -ForegroundColor Yellow
} else {
  $o = Invoke-Native { gh secret set CLOUDFLARE_API_TOKEN --repo $GithubRepo --body $CfToken }
  Assert-Ok "gh secret set CLOUDFLARE_API_TOKEN" $o
  Write-Ok "secret CLOUDFLARE_API_TOKEN"
}

Write-Host "`nBootstrap complete." -ForegroundColor Green
Write-Host "  state bucket : s3://$StateBucket"
Write-Host "  roles        : $TfRole, $CiRole"
Write-Host "  trusts       : $($RepoSubs -join '  |  ')"
Write-Host "  next         : terraform/ (Phase 2)"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
