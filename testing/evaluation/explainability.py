import os
import json
from typing import Dict, Any, List

class ExplainerPipeline:
    """
    SasyaAI Explainability Explainer Engine.
    Simulates SHAP feature importances and decision DAGs for crop recommendations.
    """
    def __init__(self):
        # Base feature weights representing soil Card parameters influence
        self.feature_names = ["soil_nitrogen", "soil_phosphorus", "soil_potassium", "soil_ph", "water_capacity"]

    def calculate_shap_values(self, soil_metrics: Dict[str, float], chosen_crop: str) -> Dict[str, float]:
        """
        Simulate SHAP values showing feature contribution weights toward a crop decision.
        Returns a map of Feature -> SHAP Importance (values range between -1.0 and +1.0)
        """
        ph = soil_metrics.get("ph", 7.0)
        nitrogen = soil_metrics.get("nitrogen", 45.0)
        phosphorus = soil_metrics.get("phosphorus", 22.0)
        potassium = soil_metrics.get("potassium", 115.0)
        water = soil_metrics.get("water_holding_capacity", 40.0)

        shap_values = {}

        if chosen_crop.lower() in ["paddy", "rice"]:
            # Paddy favors acidic soils and high water holding capacity
            shap_values["soil_ph"] = 0.4 if ph < 6.2 else -0.3
            shap_values["water_capacity"] = 0.5 if water > 35.0 else -0.4
            shap_values["soil_nitrogen"] = 0.1
            shap_values["soil_phosphorus"] = 0.05
            shap_values["soil_potassium"] = 0.05
        elif chosen_crop.lower() == "cotton":
            # Cotton favors alkaline soils
            shap_values["soil_ph"] = 0.5 if ph > 7.5 else -0.4
            shap_values["water_capacity"] = -0.2
            shap_values["soil_nitrogen"] = 0.2
            shap_values["soil_phosphorus"] = 0.1
            shap_values["soil_potassium"] = 0.1
        else:
            # Maize / Wheat general weights
            shap_values["soil_ph"] = 0.2 if (6.0 <= ph <= 7.2) else -0.2
            shap_values["water_capacity"] = 0.2 if water > 30.0 else -0.1
            shap_values["soil_nitrogen"] = 0.4 if nitrogen > 40.0 else -0.4
            shap_values["soil_phosphorus"] = 0.3 if phosphorus > 20.0 else -0.3
            shap_values["soil_potassium"] = 0.1

        return shap_values

    def generate_decision_dag(self, agristack_id: str, chosen_crop: str, shap_values: Dict[str, float]) -> Dict[str, Any]:
        """
        Creates a structured Decision Directed Acyclic Graph (DAG) explaining the decision trajectory.
        """
        nodes = [
            {"id": "START", "label": "Initialize Farmer Digital Twin profile retrieval"},
            {"id": "SOIL_INPUT", "label": "Soil Health Registry features mapped"},
            {"id": "CONSTRAINTS_CHECK", "label": "OR-Tools resource boundary limits checked"}
        ]
        edges = [
            {"from": "START", "to": "SOIL_INPUT"},
            {"from": "SOIL_INPUT", "to": "CONSTRAINTS_CHECK"}
        ]

        # Append explanation nodes dynamically based on SHAP importances
        major_contributors = [feat for feat, val in shap_values.items() if val > 0.25]
        for idx, feat in enumerate(major_contributors):
            node_id = f"EXP_{feat.upper()}"
            nodes.append({
                "id": node_id,
                "label": f"Positive driver: {feat.replace('_', ' ').title()} contributed +{shap_values[feat]:.2f} weight"
            })
            edges.append({"from": "SOIL_INPUT", "to": node_id})
            edges.append({"from": node_id, "to": "DECISION"})

        nodes.append({"id": "DECISION", "label": f"Recommend planting target: {chosen_crop}"})
        edges.append({"from": "SOIL_INPUT", "to": "DECISION"})
        edges.append({"from": "CONSTRAINTS_CHECK", "to": "DECISION"})

        return {
            "agristack_id": agristack_id,
            "crop": chosen_crop,
            "dag": {
                "nodes": nodes,
                "edges": edges
            }
        }

class HallucinationValidator:
    """
    RAG Safety Guardrails.
    Evaluates response overlap metrics against trusted context documents.
    """
    def check_hallucination_score(self, query_response: str, context_documents: List[str]) -> float:
        """
        Simple Jaccard semantic overlap check between source text and LLM advice.
        Returns a score between 0.0 (high hallucination) and 1.0 (strict compliance).
        """
        if not query_response or not context_documents:
            return 0.0

        response_words = set(query_response.lower().split())
        
        # Merge all context words
        context_words = set()
        for doc in context_documents:
            context_words.update(doc.lower().split())

        intersection = response_words.intersection(context_words)
        if not response_words:
            return 0.0
            
        overlap = len(intersection) / len(response_words)
        return round(overlap, 3)

class ExpertEscalationWorkflow:
    """
    Human-In-The-Loop (HITL) Workflow Router.
    Routes low confidence outputs to agricultural extension officers.
    """
    def process_escalation(self, agristack_id: str, query: str, confidence_score: float, hallucination_score: float) -> Dict[str, Any]:
        needs_expert = confidence_score < 0.80 or hallucination_score < 0.40
        
        return {
            "agristack_id": agristack_id,
            "query": query,
            "status": "ESCALATED_TO_EXPERT" if needs_expert else "AUTO_APPROVED",
            "assigned_officer_id": "OFFICER_VIKRAM_99" if needs_expert else None,
            "escalation_reason": "Low confidence score" if confidence_score < 0.80 else ("High hallucination threat" if hallucination_score < 0.40 else None)
        }


# ==============================================================================
# Execution Test script
# ==============================================================================

if __name__ == "__main__":
    print("Initializing SasyaAI AI Validation & Explainability Pipeline...")
    
    explainer = ExplainerPipeline()
    validator = HallucinationValidator()
    hitl = ExpertEscalationWorkflow()

    # Simulated Inputs
    soil = {"nitrogen": 25.0, "phosphorus": 12.0, "potassium": 120.0, "ph": 5.8, "water_holding_capacity": 42.0}
    crop = "Paddy"
    
    # 1. SHAP Evaluation
    shap_vals = explainer.calculate_shap_values(soil, crop)
    print(f"\n1. Calculated SHAP contributions: {json.dumps(shap_vals, indent=2)}")

    # 2. Decision DAG
    dag = explainer.generate_decision_dag("AGRI-TEST-100", crop, shap_vals)
    print(f"\n2. Explainer Decision DAG nodes count: {len(dag['dag']['nodes'])}")

    # 3. Guardrails overlaps
    context = ["Under the PM-KISAN scheme, eligible smallholder farmers receive income support of ₹6,000."]
    response = "You get 6000 rupees direct bank transfers."
    h_score = validator.check_hallucination_score(response, context)
    print(f"\n3. Hallucination Compliance Score: {h_score}")

    # 4. Expert Escalation Routing
    route = hitl.process_escalation("AGRI-TEST-100", "Where is my KCC card subsidy?", 0.72, h_score)
    print(f"\n4. Escalation status: {route['status']} (Assigned: {route['assigned_officer_id']})")
