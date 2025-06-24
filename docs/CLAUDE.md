# Blacksmith Atlas - Project Guidelines

## Project Overview
Blacksmith Atlas - Technical Design Document
Version 1.0 | Blacksmith VFX Company
Executive Summary
Blacksmith Atlas represents a comprehensive, object-oriented ecosystem designed to unify asset management, AI-powered toolsets, and production workflows across the VFX pipeline. Built on scalable architecture principles, Atlas serves as the central nervous system for Blacksmith VFX operations, spanning from creative asset libraries to AI-driven production tools.

Core Philosophy: Everything is an object. Every tool, asset, workflow, and interaction follows consistent object-oriented patterns to ensure maximum scalability, maintainability, and extensibility.

System Architecture Overview
Technology Stack
Frontend: React + Electron (Desktop Application)
Backend: Python (FastAPI/Django REST Framework)
In-App Panels: PyQt5/6 (Houdini, Maya, Nuke, Flame integration)
Database: PostgreSQL (Primary), Redis (Caching/Sessions)
File Storage: AWS S3/MinIO for assets, local NAS for active projects
AI Backend: ComfyUI integration via REST APIs
Message Queue: Celery + Redis for background tasks
Core Object Hierarchy
BaseAtlasObject
├── AssetObject
│   ├── GeometryAsset (USD, OBJ, FBX)
│   ├── MaterialAsset (Redshift, Arnold, etc.)
│   ├── TextureAsset (EXR, PNG, TIFF)
│   └── LightRigAsset
├── WorkflowObject
│   ├── RenderWorkflow
│   ├── CompositingWorkflow
│   └── AssetCreationWorkflow
├── ProjectObject
│   ├── ProjectMetadata
│   ├── ProjectAssets
│   └── ProjectTimeline
├── AIToolObject
│   ├── ImageProcessingTool
│   ├── AssetGenerationTool
│   └── BidAnalysisTool
└── UserObject
    ├── Artist
    ├── Producer
    └── Administrator
Module 1: Asset Library System
Core Components
AssetManager Class
python
class AssetManager(BaseAtlasObject):
    def __init__(self):
        self.asset_registry = AssetRegistry()
        self.version_controller = VersionController()
        self.metadata_manager = MetadataManager()
        self.format_handlers = FormatHandlerFactory()
    
    def register_asset(self, asset: AssetObject) -> str
    def retrieve_asset(self, asset_id: str) -> AssetObject
    def update_asset(self, asset_id: str, updates: dict) -> bool
    def delete_asset(self, asset_id: str) -> bool
    def search_assets(self, query: SearchQuery) -> List[AssetObject]
AssetObject Base Class
python
class AssetObject(BaseAtlasObject):
    def __init__(self, name, asset_type, file_path):
        self.id = generate_uuid()
        self.name = name
        self.asset_type = asset_type
        self.file_path = file_path
        self.metadata = AssetMetadata()
        self.dependencies = []
        self.versions = VersionHistory()
        self.tags = TagSystem()
        self.preview_data = PreviewGenerator()
    
    def validate(self) -> ValidationResult
    def generate_preview(self) -> PreviewData
    def export_to_format(self, target_format: str) -> ExportResult
    def get_dependencies(self) -> List[AssetObject]
Format Support Architecture
FormatHandler Pattern
python
class FormatHandler(ABC):
    @abstractmethod
    def can_handle(self, file_path: str) -> bool
    
    @abstractmethod
    def import_asset(self, file_path: str) -> AssetObject
    
    @abstractmethod
    def export_asset(self, asset: AssetObject, target_path: str) -> bool

class USDHandler(FormatHandler):
    # USD-specific implementation
    
class RedshiftMaterialHandler(FormatHandler):
    # Redshift material handling
Scalability Features
Lazy Loading: Assets load metadata first, full data on demand
Caching Strategy: Redis-based caching for frequently accessed assets
Distributed Storage: Assets distributed across multiple storage nodes
Search Indexing: Elasticsearch integration for complex asset queries
Version Management: Git-like versioning system for all assets
Module 2: AI-Powered Toolset
AIToolManager Architecture
python
class AIToolManager(BaseAtlasObject):
    def __init__(self):
        self.comfy_ui_client = ComfyUIClient()
        self.tool_registry = AIToolRegistry()
        self.job_queue = JobQueueManager()
        self.result_cache = ResultCacheManager()
    
    def execute_tool(self, tool_name: str, inputs: dict) -> AIJobResult
    def get_tool_status(self, job_id: str) -> JobStatus
    def register_custom_tool(self, tool: AIToolObject) -> bool
AI Tool Object Pattern
python
class AIToolObject(BaseAtlasObject):
    def __init__(self, name, comfy_workflow_path):
        self.name = name
        self.workflow_definition = self.load_workflow(comfy_workflow_path)
        self.input_schema = self.parse_input_requirements()
        self.output_schema = self.parse_output_format()
        self.execution_requirements = ExecutionRequirements()
    
    def validate_inputs(self, inputs: dict) -> ValidationResult
    def execute(self, inputs: dict) -> AIJobResult
    def estimate_execution_time(self, inputs: dict) -> timedelta
ComfyUI Integration Layer
python
class ComfyUIClient:
    def __init__(self, server_url, api_key):
        self.server_url = server_url
        self.api_key = api_key
        self.session_manager = SessionManager()
    
    def submit_workflow(self, workflow: dict, inputs: dict) -> str
    def get_job_status(self, job_id: str) -> JobStatus
    def download_results(self, job_id: str) -> ResultBundle
    def cancel_job(self, job_id: str) -> bool
Scalability Features
Job Queue System: Celery-based distributed task processing
Auto-scaling: Dynamic ComfyUI instance management based on load
Result Caching: Intelligent caching of AI-generated content
Batch Processing: Queue multiple jobs for efficient processing
Resource Management: GPU/CPU allocation optimization
Module 3: 2D Integration Tools
NukeIntegration Class
python
class NukeIntegration(DCCIntegration):
    def __init__(self):
        super().__init__("Nuke")
        self.node_factory = NukeNodeFactory()
        self.asset_importer = NukeAssetImporter()
        self.script_manager = NukeScriptManager()
    
    def import_asset(self, asset: AssetObject) -> NukeNode
    def create_asset_node(self, asset: AssetObject) -> NukeNode
    def batch_import_assets(self, assets: List[AssetObject]) -> List[NukeNode]
    def export_comp_data(self) -> CompositingData
FlameIntegration Class
python
class FlameIntegration(DCCIntegration):
    def __init__(self):
        super().__init__("Flame")
        self.media_hub = FlameMediaHub()
        self.timeline_manager = FlameTimelineManager()
        self.effect_manager = FlameEffectManager()
    
    def import_elements(self, elements: List[AssetObject]) -> List[FlameClip]
    def create_timeline_structure(self, project: ProjectObject) -> FlameTimeline
    def apply_asset_effects(self, clip: FlameClip, effects: List[EffectObject])
PyQt Panel Architecture
python
class AtlasPanelBase(QWidget):
    def __init__(self, dcc_name):
        super().__init__()
        self.dcc_name = dcc_name
        self.atlas_client = AtlasAPIClient()
        self.asset_browser = AssetBrowserWidget()
        self.tool_palette = ToolPaletteWidget()
        self.init_ui()
    
    def init_ui(self):
        # Common UI initialization
        pass
    
    def refresh_assets(self):
        # Refresh asset display
        pass
    
    def import_selected_assets(self):
        # Import selected assets to DCC
        pass
Module 4: Producer Tools
BidAnalyzer Class
python
class BidAnalyzer(AIToolObject):
    def __init__(self):
        super().__init__("BidAnalyzer", "bid_analysis_workflow.json")
        self.project_estimator = ProjectEstimator()
        self.resource_calculator = ResourceCalculator()
        self.timeline_analyzer = TimelineAnalyzer()
    
    def analyze_bid(self, bid_document: Document) -> BidAnalysisResult
    def estimate_project_scope(self, requirements: ProjectRequirements) -> ScopeEstimate
    def calculate_resource_needs(self, scope: ScopeEstimate) -> ResourcePlan
    def generate_timeline(self, resource_plan: ResourcePlan) -> ProjectTimeline
ProjectEstimator Architecture
python
class ProjectEstimator(BaseAtlasObject):
    def __init__(self):
        self.historical_data = HistoricalProjectData()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.cost_calculator = CostCalculator()
    
    def estimate_duration(self, project_scope: ProjectScope) -> timedelta
    def estimate_cost(self, project_scope: ProjectScope) -> CostBreakdown
    def estimate_team_size(self, project_scope: ProjectScope) -> TeamRequirements
    def generate_risk_assessment(self, project_scope: ProjectScope) -> RiskAnalysis
Scalability Features
Machine Learning: Historical project data training for better estimates
Template System: Reusable project templates and estimation models
Integration APIs: Connect with project management tools (Shotgun, Ftrack)
Real-time Updates: Live project tracking and estimate refinement
Module 5: Blacksmith Chatbot
ChatbotCore Architecture
python
class BlacksmithChatbot(BaseAtlasObject):
    def __init__(self):
        self.knowledge_base = BlacksmithKnowledgeBase()
        self.nlp_processor = NLPProcessor()
        self.context_manager = ConversationContextManager()
        self.workflow_assistant = WorkflowAssistant()
    
    def process_query(self, user_input: str, context: ConversationContext) -> ChatResponse
    def suggest_workflows(self, user_intent: Intent) -> List[WorkflowSuggestion]
    def explain_terminology(self, term: str) -> TerminologyExplanation
    def provide_asset_recommendations(self, criteria: dict) -> List[AssetObject]
Knowledge Base Structure
python
class BlacksmithKnowledgeBase:
    def __init__(self):
        self.terminology_db = TerminologyDatabase()
        self.workflow_db = WorkflowDatabase()
        self.asset_relationships = AssetRelationshipGraph()
        self.best_practices = BestPracticesLibrary()
    
    def search_knowledge(self, query: str) -> List[KnowledgeItem]
    def update_knowledge(self, new_info: KnowledgeItem) -> bool
    def get_related_concepts(self, concept: str) -> List[str]
Scalability Features
Learning System: Continuous learning from user interactions
Multi-modal Interface: Text, voice, and visual query support
Context Awareness: Understanding of current project and user role
Integration Points: Deep integration with all Atlas modules
Data Architecture & Database Design
Primary Database Schema (PostgreSQL)
sql
-- Core Tables
CREATE TABLE atlas_objects (
    id UUID PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE assets (
    id UUID PRIMARY KEY REFERENCES atlas_objects(id),
    file_path VARCHAR(500),
    file_size BIGINT,
    file_format VARCHAR(50),
    preview_path VARCHAR(500),
    version_number INTEGER DEFAULT 1,
    parent_asset_id UUID REFERENCES assets(id)
);

CREATE TABLE projects (
    id UUID PRIMARY KEY REFERENCES atlas_objects(id),
    status VARCHAR(50),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12,2),
    client_id UUID
);

CREATE TABLE ai_jobs (
    id UUID PRIMARY KEY,
    tool_name VARCHAR(100),
    status VARCHAR(50),
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
Caching Strategy (Redis)
Asset Metadata: Cache frequently accessed asset information
User Sessions: Store user authentication and preferences
Search Results: Cache complex search query results
AI Job Status: Real-time job status tracking
API Architecture
RESTful API Design
python
class AtlasAPIRouter:
    """Main API router for Blacksmith Atlas"""
    
    # Asset Management Endpoints
    @router.get("/api/v1/assets")
    async def list_assets(filters: AssetFilters = None) -> List[AssetObject]
    
    @router.post("/api/v1/assets")
    async def create_asset(asset_data: AssetCreateRequest) -> AssetObject
    
    @router.get("/api/v1/assets/{asset_id}")
    async def get_asset(asset_id: str) -> AssetObject
    
    # AI Tools Endpoints
    @router.post("/api/v1/ai-tools/{tool_name}/execute")
    async def execute_ai_tool(tool_name: str, inputs: dict) -> AIJobResult
    
    @router.get("/api/v1/ai-jobs/{job_id}/status")
    async def get_job_status(job_id: str) -> JobStatus
    
    # Project Management Endpoints
    @router.post("/api/v1/projects/{project_id}/estimate")
    async def estimate_project(project_id: str, requirements: ProjectRequirements) -> ProjectEstimate
WebSocket Integration
python
class AtlasWebSocketManager:
    """Real-time communication for Atlas clients"""
    
    async def broadcast_asset_update(self, asset_id: str, update_data: dict)
    async def notify_job_completion(self, user_id: str, job_id: str, result: AIJobResult)
    async def send_chatbot_response(self, session_id: str, response: ChatResponse)
Security & Authentication
Security Architecture
python
class SecurityManager(BaseAtlasObject):
    def __init__(self):
        self.auth_provider = AuthenticationProvider()
        self.authorization_engine = AuthorizationEngine()
        self.audit_logger = AuditLogger()
        self.encryption_service = EncryptionService()
    
    def authenticate_user(self, credentials: UserCredentials) -> AuthToken
    def authorize_action(self, user: UserObject, action: str, resource: str) -> bool
    def encrypt_sensitive_data(self, data: bytes) -> bytes
    def audit_action(self, user: UserObject, action: str, resource: str)
Role-Based Access Control
Artist Role: Asset access, AI tool usage, limited project visibility
Producer Role: Full project access, bid analysis tools, team management
Administrator Role: System configuration, user management, full access
Client Role: Limited asset preview, project status viewing
Deployment & DevOps
Container Architecture (Docker)
dockerfile
# Backend Service
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Service
FROM node:18-alpine
COPY package.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn build
CMD ["yarn", "electron"]
Kubernetes Deployment
yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atlas-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: atlas-backend
  template:
    metadata:
      labels:
        app: atlas-backend
    spec:
      containers:
      - name: atlas-backend
        image: blacksmith/atlas-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: atlas-secrets
              key: database-url
Scalability Roadmap
Phase 1: Foundation (Months 1-6)
Core object-oriented architecture implementation
Basic asset management system
Simple AI tool integration
PyQt panels for primary DCCs
Phase 2: Integration (Months 7-12)
Advanced AI toolset with ComfyUI
Full 2D integration (Nuke/Flame)
Producer tools and bid analysis
Basic chatbot functionality
Phase 3: Intelligence (Months 13-18)
Machine learning integration
Advanced chatbot with deep knowledge
Predictive analytics for projects
Automated workflow suggestions
Phase 4: Expansion (Months 19-24)
Cloud deployment options
Multi-studio collaboration features
Advanced AI model training
Third-party plugin ecosystem
Performance Metrics & Monitoring
Key Performance Indicators
python
class PerformanceMonitor(BaseAtlasObject):
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboard = PerformanceDashboard()
    
    def track_asset_load_time(self, asset_id: str, load_time: float)
    def track_ai_job_duration(self, tool_name: str, duration: float)
    def track_user_activity(self, user_id: str, action: str)
    def generate_performance_report(self) -> PerformanceReport
Monitoring Targets
Asset Load Time: < 2 seconds for metadata, < 10 seconds for full assets
AI Job Queue: < 30 seconds average wait time
API Response Time: < 500ms for standard queries
System Uptime: > 99.5% availability
User Satisfaction: > 4.5/5 average rating
Risk Management & Mitigation
Technical Risks
AI Service Downtime: Implement fallback AI services and local processing
Database Corruption: Automated backups every 4 hours with point-in-time recovery
Storage Failures: Distributed storage with 3x replication
Performance Degradation: Auto-scaling and load balancing
Business Risks
User Adoption: Comprehensive training and gradual rollout
Data Security: End-to-end encryption and audit trails
Vendor Dependencies: Multiple service providers and exit strategies
Scalability Limits: Microservices architecture for independent scaling
Testing Strategy
Automated Testing Framework
python
class AtlasTestSuite:
    def __init__(self):
        self.unit_tests = UnitTestRunner()
        self.integration_tests = IntegrationTestRunner()
        self.performance_tests = PerformanceTestRunner()
        self.security_tests = SecurityTestRunner()
    
    def run_full_suite(self) -> TestResults
    def run_continuous_tests(self) -> bool
    def generate_test_report(self) -> TestReport
Testing Coverage Targets
Unit Tests: > 90% code coverage
Integration Tests: All API endpoints and workflows
Performance Tests: Load testing with 100+ concurrent users
Security Tests: Automated vulnerability scanning
Maintenance & Support
Support Tier Structure
Tier 1: Basic user support and common issues
Tier 2: Technical issues and workflow problems
Tier 3: Advanced troubleshooting and development support
Emergency: Critical system failures (24/7 response)
Update Management
python
class UpdateManager(BaseAtlasObject):
    def __init__(self):
        self.version_controller = VersionController()
        self.deployment_manager = DeploymentManager()
        self.rollback_manager = RollbackManager()
    
    def check_for_updates(self) -> List[AvailableUpdate]
    def deploy_update(self, update: UpdatePackage) -> DeploymentResult
    def rollback_update(self, version: str) -> RollbackResult
Conclusion
Blacksmith Atlas represents a comprehensive, object-oriented approach to VFX pipeline management. By maintaining consistent architectural patterns across all modules and emphasizing scalability from the ground up, Atlas will serve as the foundation for Blacksmith VFX's continued growth and innovation.

The modular design ensures that each component can evolve independently while maintaining system coherence. The object-oriented approach provides clear interfaces for extension and customization, allowing the system to adapt to changing industry needs and emerging technologies.

This design document serves as the north star for development, ensuring all implementation decisions align with the core principles of scalability, maintainability, and user-centric design.

Document Version: 1.0
Last Updated: June 2025
Next Review: September 2025



## Architecture
- **Backend**: Python FastAPI application in `/backend`
- **Frontend**: React/Vite application in `/frontend` 
- **Electron**: Desktop app wrapper in `/electron`

## Development Setup

### Virtual Environment
1. **Create virtual environment**: `python3 -m venv venv`
2. **Activate virtual environment**: `source venv/bin/activate`
3. **Install Python dependencies**: `python3 -m pip install fastapi uvicorn pydantic PyYAML SQLAlchemy`

### Running the Application
**Super Simple One-Command Start:**
- **Everything**: Just run `npm run dev` from the root directory
  - Automatically kills any existing processes on ports 3011 and 8000
  - Starts backend (FastAPI on port 8000) with virtual environment
  - Starts frontend (Vite on port 3011)
  - Opens Electron desktop app
  - When you close the Electron window, all processes are automatically killed

**Individual Services:**
- **Backend only**: `npm run backend`
- **Frontend only**: `npm run frontend`
- **Electron only**: `npm run electron`
- **Clean up ports**: `npm run cleanup`

### PyCharm Setup
- Set Python interpreter to the virtual environment: `venv/bin/python`

## Key Components
- Asset Management System
- Delivery Tool with CSV parsing and TTG generation
- AI Tools integration
- Producer Tools

## Development Guidelines
[Add your specific coding standards, conventions, and guidelines here]

## Testing
[Add your testing approach and commands here]

## Deployment
[Add deployment instructions here]

## Notes
I am writing my Backend Code in Python, My frontend with React, and using Electron for my application look.

I am writing my code in Pycharm. And all my terminal commands Im using through pycharm.
- Migrated from Windows to Mac environment
- Uses PyCharm as primary IDE