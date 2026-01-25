import json
from datetime import datetime, timezone
from decimal import Decimal

import anthropic

from domain.ports.llm_repository import (
    LLMRepository,
    RiskAnalysis,
    PortfolioInterpretation,
    AllocationInterpretation,
    SecuritySummary,
)


class AnthropicLLMRepository(LLMRepository):
    """Anthropic Claude implementation of LLMRepository."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def analyze_portfolio_risks(
        self,
        portfolio_summary: dict,
        holdings: list[dict],
    ) -> RiskAnalysis:
        """Analyze portfolio risks using Claude with web search for macro context."""

        # Build holdings summary for the prompt
        holdings_text = self._format_holdings(holdings)
        portfolio_text = self._format_portfolio_summary(portfolio_summary)

        # First, get macro economic context using web search
        macro_context = self._get_macro_context(holdings)

        # Now analyze risks with the macro context
        prompt = f"""You are a professional portfolio risk analyst. Analyze the following investment portfolio and identify potential risks.

## Portfolio Summary
{portfolio_text}

## Holdings Detail
{holdings_text}

## Current Macro Economic Context
{macro_context}

Based on this information, provide a comprehensive risk analysis. For each risk identified, include:
1. Risk category (e.g., "Market Risk", "Concentration Risk", "Interest Rate Risk", "Currency Risk", "Sector Risk", "Liquidity Risk", "Inflation Risk", "Geopolitical Risk")
2. Severity level (High, Medium, Low)
3. Description of the specific risk
4. Which holdings are affected
5. Potential impact on the portfolio
6. Suggested mitigation strategies

Return your analysis as a JSON object with the following structure:
{{
  "risks": [
    {{
      "category": "string",
      "severity": "High|Medium|Low",
      "title": "string (short title)",
      "description": "string (detailed explanation)",
      "affected_holdings": ["ticker1", "ticker2"],
      "potential_impact": "string",
      "mitigation": "string"
    }}
  ],
  "macro_summary": "string (2-3 sentence summary of current macro environment's impact on this portfolio)"
}}

Identify at least 3-5 relevant risks based on the portfolio composition and current market conditions. Be specific and actionable."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        # Parse the response
        response_text = response.content[0].text

        # Extract JSON from response (handle potential markdown code blocks)
        json_str = self._extract_json(response_text)
        result = json.loads(json_str)

        return RiskAnalysis(
            risks=result.get("risks", []),
            macro_climate_summary=result.get("macro_summary", ""),
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            model_used=self._model,
        )

    def _get_macro_context(self, holdings: list[dict]) -> str:
        """Get current macro economic context relevant to the portfolio."""
        # Extract unique asset types and sectors
        asset_types = set(h.get("asset_type", "equity") for h in holdings)
        sectors = set(h.get("sector", "") for h in holdings if h.get("sector"))

        # Build search context
        search_topics = []
        if "bond" in asset_types:
            search_topics.append("interest rates and bond market outlook")
        if "equity" in asset_types:
            search_topics.append("stock market trends and outlook")
        for sector in list(sectors)[:3]:  # Limit to 3 sectors
            search_topics.append(f"{sector} sector outlook")

        search_query = f"current economic outlook 2024 {' '.join(search_topics[:3])}"

        # Use Claude to generate macro context (simulated web search through model knowledge)
        prompt = f"""Based on your knowledge of current economic conditions and market trends, provide a brief summary of the macro economic environment relevant to an investment portfolio containing:
- Asset types: {', '.join(asset_types)}
- Sectors: {', '.join(list(sectors)[:5]) if sectors else 'Diversified'}

Focus on:
1. Current interest rate environment and Federal Reserve policy
2. Inflation trends
3. Key economic indicators (GDP growth, unemployment)
4. Relevant sector-specific factors
5. Geopolitical risks affecting markets

Provide a concise 3-4 paragraph summary of the current macro environment and its implications for investors."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.content[0].text

    def _format_holdings(self, holdings: list[dict]) -> str:
        """Format holdings list for the prompt."""
        if not holdings:
            return "No holdings in portfolio."

        lines = []
        for h in holdings:
            line = (
                f"- {h.get('ticker', 'N/A')} ({h.get('name', 'Unknown')}): "
                f"{h.get('asset_type', 'equity')} | {h.get('asset_class', 'N/A')} | "
                f"{h.get('sector', 'N/A')} | "
                f"Value: ${h.get('market_value', 0):,.2f} | "
                f"Weight: {h.get('weight', 0):.1f}%"
            )
            lines.append(line)
        return "\n".join(lines)

    def _format_portfolio_summary(self, summary: dict) -> str:
        """Format portfolio summary for the prompt."""
        lines = [
            f"Total Value: ${summary.get('total_value', 0):,.2f}",
            f"Total Cost Basis: ${summary.get('total_cost', 0):,.2f}",
            f"Unrealized Gain/Loss: ${summary.get('total_gain_loss', 0):,.2f} ({summary.get('total_gain_loss_percent', 0):.1f}%)",
            f"Number of Holdings: {summary.get('holdings_count', 0)}",
            "",
            "Asset Type Allocation:",
        ]

        for item in summary.get("by_asset_type", []):
            lines.append(f"  - {item['name']}: {item['percentage']:.1f}%")

        lines.append("")
        lines.append("Asset Class Allocation:")
        for item in summary.get("by_asset_class", []):
            lines.append(f"  - {item['name']}: {item['percentage']:.1f}%")

        lines.append("")
        lines.append("Sector Allocation:")
        for item in summary.get("by_sector", []):
            lines.append(f"  - {item['name']}: {item['percentage']:.1f}%")

        return "\n".join(lines)

    def _extract_json(self, text: str) -> str:
        """Extract JSON from response text, handling markdown code blocks."""
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        # Try to find raw JSON object
        elif "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return text[start:end]
        return text

    def interpret_portfolio_description(
        self,
        description: str,
        available_securities: list[SecuritySummary],
    ) -> PortfolioInterpretation:
        """Interpret a natural language portfolio description into allocations."""

        # Format available securities for the prompt
        securities_text = self._format_available_securities(available_securities)

        prompt = f"""You are a financial advisor helping to interpret a user's portfolio description and map it to specific securities.

## User's Portfolio Description
{description}

## Available Securities in Our Registry
{securities_text}

## Your Task
Based on the user's description, select the most appropriate securities from our registry and assign weights (percentages) that total 100%.

Guidelines:
1. Map general descriptions to specific tickers (e.g., "S&P 500 index fund" -> SPY or VOO, "tech stocks" -> QQQ or specific tech ETFs/stocks)
2. If the user mentions a specific percentage, use it. Otherwise, infer reasonable weights.
3. If the user's description doesn't add up to 100%, adjust proportionally or fill gaps with diversified options.
4. If you cannot find a matching security, note it in the unmatched list.
5. Prefer ETFs for broad market exposure and individual stocks for specific companies.

Return your response as JSON with this structure:
{{
  "allocations": [
    {{
      "ticker": "string (exact ticker from available securities)",
      "display_name": "string (name of the security)",
      "weight": number (percentage, 0-100)
    }}
  ],
  "unmatched_descriptions": ["string (parts of description that couldn't be matched)"]
}}

Important:
- Weights MUST sum to exactly 100
- Only use tickers from the available securities list
- Be specific and practical in your allocations"""

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            response_text = response.content[0].text
        except anthropic.AuthenticationError:
            return PortfolioInterpretation(
                allocations=[],
                unmatched_descriptions=["LLM authentication failed - check API key"],
                model_used=self._model,
            )
        except anthropic.APIError as e:
            return PortfolioInterpretation(
                allocations=[],
                unmatched_descriptions=[f"LLM API error: {str(e)}"],
                model_used=self._model,
            )
        json_str = self._extract_json(response_text)

        try:
            result = json.loads(json_str)
        except json.JSONDecodeError:
            return PortfolioInterpretation(
                allocations=[],
                unmatched_descriptions=["Failed to parse LLM response"],
                model_used=self._model,
            )

        allocations = []
        for alloc in result.get("allocations", []):
            try:
                allocations.append(
                    AllocationInterpretation(
                        ticker=alloc.get("ticker", ""),
                        display_name=alloc.get("display_name", ""),
                        weight=Decimal(str(alloc.get("weight", 0))),
                    )
                )
            except (ValueError, TypeError):
                continue

        return PortfolioInterpretation(
            allocations=allocations,
            unmatched_descriptions=result.get("unmatched_descriptions", []),
            model_used=self._model,
        )

    def _format_available_securities(self, securities: list[SecuritySummary]) -> str:
        """Format available securities for the LLM prompt."""
        if not securities:
            return "No securities available."

        lines = []
        for s in securities:
            sector = s.sector if s.sector else "N/A"
            line = (
                f"- {s.ticker}: {s.display_name} | "
                f"Type: {s.asset_type} | Sector: {sector}"
            )
            lines.append(line)
        return "\n".join(lines)
