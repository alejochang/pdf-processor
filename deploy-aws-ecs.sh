#!/bin/bash

# AWS ECS Deployment Script for PDF Processor
# Prerequisites: AWS CLI installed and configured

set -e

# Configuration
AWS_REGION="us-east-1"
CLUSTER_NAME="pdf-processor-cluster"
SERVICE_NAME="pdf-processor-service"
TASK_FAMILY="pdf-processor"
ECR_REPO_BACKEND="pdf-processor-backend"
ECR_REPO_FRONTEND="pdf-processor-frontend"
ECR_REPO_WORKER="pdf-processor-worker"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=== AWS ECS Deployment for PDF Processor ==="
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo ""

# Step 1: Create ECR repositories
echo "Step 1: Creating ECR repositories..."
for repo in $ECR_REPO_BACKEND $ECR_REPO_FRONTEND $ECR_REPO_WORKER; do
    aws ecr create-repository \
        --repository-name $repo \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true \
        2>/dev/null || echo "Repository $repo already exists"
done

# Step 2: Build and push Docker images
echo ""
echo "Step 2: Building and pushing Docker images..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
echo "Building backend..."
docker build -t $ECR_REPO_BACKEND:latest ./backend
docker tag $ECR_REPO_BACKEND:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_BACKEND:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_BACKEND:latest

# Build and push frontend
echo "Building frontend..."
docker build -t $ECR_REPO_FRONTEND:latest ./frontend-nextjs
docker tag $ECR_REPO_FRONTEND:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_FRONTEND:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_FRONTEND:latest

# Build and push worker
echo "Building worker..."
docker build -t $ECR_REPO_WORKER:latest -f ./backend/Dockerfile ./backend
docker tag $ECR_REPO_WORKER:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_WORKER:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_WORKER:latest

# Step 3: Create ECS cluster
echo ""
echo "Step 3: Creating ECS cluster..."
aws ecs create-cluster \
    --cluster-name $CLUSTER_NAME \
    --region $AWS_REGION \
    2>/dev/null || echo "Cluster $CLUSTER_NAME already exists"

# Step 4: Create task execution role
echo ""
echo "Step 4: Creating task execution role..."
ROLE_NAME="ecsTaskExecutionRole"

aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || echo "Role already exists"

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
    2>/dev/null || true

# Step 5: Create CloudWatch log groups
echo ""
echo "Step 5: Creating CloudWatch log groups..."
for service in backend frontend worker redis; do
    aws logs create-log-group \
        --log-group-name /ecs/pdf-processor/$service \
        --region $AWS_REGION \
        2>/dev/null || echo "Log group for $service already exists"
done

# Step 6: Register task definition
echo ""
echo "Step 6: Registering ECS task definition..."
cat > task-definition.json << EOF
{
    "family": "$TASK_FAMILY",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "1024",
    "memory": "2048",
    "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME",
    "containerDefinitions": [
        {
            "name": "redis",
            "image": "redis:7-alpine",
            "essential": true,
            "portMappings": [{"containerPort": 6379}],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/pdf-processor/redis",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "redis"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "redis-cli ping || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3
            }
        },
        {
            "name": "backend",
            "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_BACKEND:latest",
            "essential": true,
            "portMappings": [{"containerPort": 8000}],
            "environment": [
                {"name": "REDIS_URL", "value": "redis://localhost:6379"},
                {"name": "GOOGLE_API_KEY", "value": "AIzaSyDxQWdpHhxe0SckdBArq19pStScZc7iMK0"},
                {"name": "MISTRAL_API_KEY", "value": "0mmezs4ZhtCrOwBkEgLQ58kNl8O1AFjO"},
                {"name": "MAX_FILE_SIZE_MB", "value": "25"}
            ],
            "dependsOn": [{"containerName": "redis", "condition": "HEALTHY"}],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/pdf-processor/backend",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "backend"
                }
            }
        },
        {
            "name": "worker",
            "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_WORKER:latest",
            "essential": true,
            "command": ["python", "-m", "app.worker"],
            "environment": [
                {"name": "REDIS_URL", "value": "redis://localhost:6379"},
                {"name": "GOOGLE_API_KEY", "value": "AIzaSyDxQWdpHhxe0SckdBArq19pStScZc7iMK0"},
                {"name": "MISTRAL_API_KEY", "value": "0mmezs4ZhtCrOwBkEgLQ58kNl8O1AFjO"}
            ],
            "dependsOn": [{"containerName": "redis", "condition": "HEALTHY"}],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/pdf-processor/worker",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "worker"
                }
            }
        },
        {
            "name": "frontend",
            "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_FRONTEND:latest",
            "essential": true,
            "portMappings": [{"containerPort": 3000}],
            "environment": [
                {"name": "NEXT_PUBLIC_API_URL", "value": "http://localhost:8000"}
            ],
            "dependsOn": [{"containerName": "backend", "condition": "START"}],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/pdf-processor/frontend",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "frontend"
                }
            }
        }
    ]
}
EOF

aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region $AWS_REGION

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Create VPC and subnets (if not exists)"
echo "2. Create security group allowing ports 3000 and 8000"
echo "3. Create ECS service:"
echo ""
echo "   aws ecs create-service \\"
echo "       --cluster $CLUSTER_NAME \\"
echo "       --service-name $SERVICE_NAME \\"
echo "       --task-definition $TASK_FAMILY \\"
echo "       --desired-count 1 \\"
echo "       --launch-type FARGATE \\"
echo "       --network-configuration \"awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}\" \\"
echo "       --region $AWS_REGION"
echo ""
echo "4. Create Application Load Balancer (optional) for production"
