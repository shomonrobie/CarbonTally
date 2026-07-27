# backend/report_generator.py - ENHANCED VERSION

import base64
import io
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import pandas as pd
from fpdf import FPDF
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

# ============================================
# DATA CLASSES FOR STRUCTURED REPORTING
# ============================================
router = APIRouter()  # ✅ This line must be here before any @router decorators

@dataclass
class EmissionSource:
    """Represents an emission source with details."""
    activity_type: str
    scope: str
    quantity: float
    unit: str
    kg_co2e: float
    tonnes_co2e: float
    percentage: float
    asset_name: Optional[str] = None
    facility_name: Optional[str] = None

@dataclass
class YearOverYearComparison:
    """Year-over-year comparison data."""
    current_year: int
    previous_year: int
    current_emissions: float  # tonnes
    previous_emissions: float  # tonnes
    absolute_change: float
    percentage_change: float
    trend_direction: str  # 'increase', 'decrease', 'stable'
    narrative: str

@dataclass
class MethodologyNote:
    """Methodology note for the report."""
    section: str
    title: str
    description: str
    data_sources: List[str]
    calculation_method: str
    assumptions: List[str]
    limitations: List[str]

@dataclass
class EfficiencyMeasure:
    """Energy efficiency measure."""
    name: str
    category: str
    description: str
    estimated_savings_tonnes: float
    implementation_status: str  # 'planned', 'in_progress', 'completed'
    completion_date: Optional[str] = None

# ============================================
# ENHANCED HELPER FUNCTIONS
# ============================================

def sanitize_text(text):
    """Safely sanitize text for PDF generation."""
    if not text:
        return ""
    text = str(text)
    replacements = {
        '’': "'", '“': '"', '”': '"', '–': '-', '—': '-',
        '…': '...', '•': '-', '®': '(R)', '™': '(TM)'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.encode('latin-1', 'replace').decode('latin-1')
    return text

def format_currency(amount: float) -> str:
    """Format currency values."""
    if amount >= 1_000_000:
        return f"£{amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"£{amount/1_000:.1f}K"
    return f"£{amount:,.0f}"

def get_trend_color(percentage: float) -> tuple:
    """Get color for trend indicators."""
    if percentage < -5:
        return (22, 163, 74)  # Green - significant decrease
    elif percentage < 0:
        return (132, 204, 22)  # Light green - slight decrease
    elif percentage < 5:
        return (234, 179, 8)   # Yellow - stable
    elif percentage < 15:
        return (249, 115, 22)  # Orange - slight increase
    else:
        return (220, 38, 38)   # Red - significant increase

def generate_trend_arrow(percentage: float) -> str:
    """Generate trend arrow indicator."""
    if percentage < -10:
        return "↓↓"  # Strong decrease
    elif percentage < -2:
        return "↓"   # Decrease
    elif percentage < 2:
        return "→"   # Stable
    elif percentage < 10:
        return "↑"   # Increase
    else:
        return "↑↑"  # Strong increase

def calculate_intensity_ratios(total_tonnes: float, org_metadata: Dict) -> Dict:
    """
    Calculate intensity ratios based on organization metadata.
    Used for professional report generation.
    """
    ratios = {}
    
    # Per employee intensity
    employees = org_metadata.get('total_employees', 0)
    if employees > 0:
        ratios['per_employee'] = total_tonnes / employees
        ratios['per_employee_label'] = f"tonnes CO2e per employee (based on {employees} employees)"
    
    # Per revenue intensity
    revenue = org_metadata.get('annual_revenue', 0)
    if revenue > 0:
        ratios['per_million_revenue'] = total_tonnes / (revenue / 1000000)
        ratios['per_million_revenue_label'] = f"tonnes CO2e per £1M revenue (Revenue: £{revenue:,.0f})"
    
    # Per floor area intensity
    floor_area = org_metadata.get('total_floor_area_sqft', 0)
    if floor_area > 0:
        ratios['per_sqft'] = total_tonnes / floor_area
        ratios['per_sqft_label'] = f"tonnes CO2e per sqft (Total floor area: {floor_area:,.0f} sqft)"
    
    # Per facility intensity
    facilities = org_metadata.get('total_facilities', 0)
    if facilities > 0:
        ratios['per_facility'] = total_tonnes / facilities
        ratios['per_facility_label'] = f"tonnes CO2e per facility ({facilities} facilities)"
    
    return ratios

# ============================================
# ENHANCED PDF REPORT CLASS
# ============================================

class EnhancedSustainabilityReportPDF(FPDF):
    """Enhanced base class for all sustainability reports with modern styling."""
    
    def __init__(self, org_name: str, reporting_year: int, report_type: str = "SECR", 
                 company_logo: Optional[str] = None, theme_color: tuple = (22, 163, 74)):
        super().__init__()
        self.org_name = org_name
        self.reporting_year = reporting_year
        self.report_type = report_type
        self.theme_color = theme_color
        self.company_logo = company_logo
        self.set_auto_page_break(auto=True, margin=20)
        
        # Define color palette
        self.colors = {
            'primary': theme_color,
            'secondary': (15, 23, 42),
            'accent': (241, 245, 249),
            'text_dark': (15, 23, 42),
            'text_medium': (51, 65, 85),
            'text_light': (100, 116, 139),
            'success': (22, 163, 74),
            'warning': (234, 179, 8),
            'danger': (220, 38, 38),
            'white': (255, 255, 255),
        }
    
    def header(self):
        """Enhanced header with branding."""
        if self.page_no() > 1:
            # Header for pages after first
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(100, 116, 139)
            self.cell(50, 8, sanitize_text(self.org_name), 0, 0, 'L')
            self.cell(90, 8, f"{self.report_type} Report {self.reporting_year}", 0, 0, 'C')
            self.set_font('Helvetica', '', 8)
            self.cell(50, 8, f"Page {self.page_no()}", 0, 0, 'R')
            self.ln(8)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)
    
    def footer(self):
        """Enhanced footer with timestamp."""
        self.set_y(-18)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'Generated by CarbonTally | {datetime.now().strftime("%d %B %Y %H:%M")}', 0, 0, 'C')
    
    def add_cover_page(self, report_highlights: Dict):
        """Add a professional cover page."""
        self.add_page()
        
        # Decorative top bar
        self.set_fill_color(*self.colors['primary'])
        self.rect(0, 0, 210, 8, 'F')
        
        # Spacer
        self.ln(30)
        
        # Report title
        self.set_font('Helvetica', 'B', 28)
        self.set_text_color(*self.colors['secondary'])
        self.cell(0, 15, sanitize_text(self.report_type), 0, 1, 'C')
        self.set_font('Helvetica', 'B', 20)
        self.cell(0, 12, 'Sustainability Report', 0, 1, 'C')
        self.ln(5)
        
        # Organization name
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(*self.colors['primary'])
        self.cell(0, 10, sanitize_text(self.org_name), 0, 1, 'C')
        self.ln(5)
        
        # Year
        self.set_font('Helvetica', '', 14)
        self.set_text_color(*self.colors['text_medium'])
        self.cell(0, 8, f'Reporting Period: {self.reporting_year}', 0, 1, 'C')
        self.ln(15)
        
        # Key metrics box
        self.set_fill_color(*self.colors['accent'])
        self.rect(20, self.get_y() + 5, 170, 50, 'F')
        self.set_y(self.get_y() + 10)
        
        if report_highlights:
            metrics = report_highlights.get('metrics', {})
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(*self.colors['text_light'])
            self.cell(0, 8, 'KEY METRICS', 0, 1, 'C')
            self.ln(2)
            
            # Layout metrics in 3 columns
            cols = [
                f"Total Emissions: {metrics.get('total_tonnes', 0):,.0f} tCO2e",
                f"Scope 1: {metrics.get('scope1', 0):,.0f} tCO2e",
                f"Scope 2: {metrics.get('scope2', 0):,.0f} tCO2e",
                f"Scope 3: {metrics.get('scope3', 0):,.0f} tCO2e",
                f"Records: {metrics.get('records', 0)}",
                f"YoY Change: {metrics.get('yoy_change', 0):+.1f}%"
            ]
            
            self.set_font('Helvetica', '', 9)
            self.set_text_color(*self.colors['text_medium'])
            for i, text in enumerate(cols):
                x_pos = 30 + (i % 3) * 55
                if i % 3 == 0:
                    self.set_y(self.get_y() + 6)
                self.set_x(x_pos)
                self.cell(50, 6, sanitize_text(text), 0, 0, 'L')
        
        self.ln(30)
        
        # Footer text
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.colors['text_light'])
        self.cell(0, 6, 'A comprehensive sustainability report generated by CarbonTally', 0, 1, 'C')
        self.cell(0, 6, 'Compliant with SECR/CSRD/ISSB reporting standards', 0, 1, 'C')
    
    def add_section_with_border(self, title: str, content: str, 
                                 icon: str = "📊", border_color: tuple = None):
        """Add a section with a colored left border."""
        if border_color is None:
            border_color = self.colors['primary']
        
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*self.colors['secondary'])
        self.cell(8, 10, sanitize_text(icon), 0, 0, 'L')
        self.cell(0, 10, sanitize_text(title), 0, 1, 'L')
        
        self.set_draw_color(*border_color)
        self.rect(10, self.get_y() - 8, 3, self.get_y() + 2, 'F')
        
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self.colors['text_medium'])
        self.set_x(15)
        self.multi_cell(180, 6, sanitize_text(content))
        self.ln(5)
    
    def add_narrative_box(self, title: str, content: str, 
                          narrative_type: str = "methodology"):
        """Add a styled narrative box for methodology, efficiency, etc."""
        colors = {
            'methodology': (240, 253, 244),
            'efficiency': (239, 246, 255),
            'comparison': (255, 247, 237),
        }
        
        fill_color = colors.get(narrative_type, (248, 248, 248))
        self.set_fill_color(*fill_color)
        self.set_draw_color(*self.colors['primary'])
        
        # Rounded rectangle effect (approximated with standard rect)
        self.rect(10, self.get_y(), 190, self.get_string_height(20, content) + 30, 'DF')
        
        self.set_y(self.get_y() + 5)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*self.colors['secondary'])
        self.cell(0, 8, sanitize_text(title), 0, 1, 'L')
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self.colors['text_medium'])
        self.set_x(15)
        self.multi_cell(180, 5, sanitize_text(content))
        self.ln(3)
    
    def add_trend_indicator(self, percentage: float, label: str = "Year-over-Year Change"):
        """Add a visual trend indicator."""
        color = get_trend_color(percentage)
        arrow = generate_trend_arrow(percentage)
        
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*self.colors['secondary'])
        self.cell(60, 10, sanitize_text(label + ":"), 0, 0, 'L')
        
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*color)
        self.cell(80, 10, f"{arrow} {percentage:+.1f}%", 0, 1, 'L')
        
        # Add a simple visual bar
        bar_width = 60
        bar_x = 10
        bar_y = self.get_y() - 5
        
        self.set_fill_color(200, 200, 200)
        self.rect(bar_x, bar_y, bar_width, 4, 'F')
        
        # Fill based on percentage
        fill_width = (percentage / 20) * bar_width  # Scale -20% to +20% to full width
        fill_width = max(0, min(bar_width, fill_width + bar_width/2))
        self.set_fill_color(*color)
        self.rect(bar_x + bar_width/2 - fill_width/2, bar_y, fill_width, 4, 'F')
        
        self.ln(10)
    
    def add_data_table(self, headers: List[str], data: List[List], 
                       column_widths: Optional[List[int]] = None,
                       highlight_best: bool = False):
        """Enhanced data table with alternating row colors."""
        if column_widths is None:
            col_count = len(headers)
            column_widths = [190 // col_count] * col_count
        
        # Header
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(*self.colors['primary'])
        self.set_text_color(255, 255, 255)
        self.set_draw_color(*self.colors['primary'])
        
        for i, header in enumerate(headers):
            self.cell(column_widths[i], 10, sanitize_text(header), 1, 0, 'C', 1)
        self.ln()
        
        # Data rows
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.colors['text_medium'])
        fill = False
        
        # Find best value if highlighting
        best_idx = None
        if highlight_best and data and len(data) > 0 and len(data[0]) > 1:
            numeric_values = []
            for row in data:
                try:
                    val = float(str(row[1]).replace(',', ''))
                    numeric_values.append(val)
                except:
                    numeric_values.append(None)
            if any(v is not None for v in numeric_values):
                # Find max value (assuming second column is the value to highlight)
                valid_indices = [i for i, v in enumerate(numeric_values) if v is not None]
                if valid_indices:
                    best_idx = max(valid_indices, key=lambda i: numeric_values[i])
        
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                # Highlight best row
                if highlight_best and row_idx == best_idx:
                    self.set_fill_color(240, 253, 244)
                    self.set_draw_color(22, 163, 74)
                else:
                    self.set_fill_color(248, 248, 248 if fill else 255, 255, 255)
                    self.set_draw_color(200, 200, 200)
                
                self.cell(column_widths[col_idx], 8, sanitize_text(str(cell)), 1, 0, 'L', True)
            self.ln()
            fill = not fill
    
    def add_methodology_section(self, methodology_data: Dict):
        """Add a comprehensive methodology section."""
        self.add_section_title("📋 Methodology")
        
        # Overview
        self.add_subsection_title("1. Overview")
        self.add_paragraph(methodology_data.get('overview', 'Emissions calculated using standard methodologies.'))
        self.ln(3)
        
        # Calculation method
        self.add_subsection_title("2. Calculation Method")
        self.add_paragraph(methodology_data.get('calculation_method', 'DEFRA conversion factors used.'))
        self.ln(3)
        
        # Data sources
        self.add_subsection_title("3. Data Sources")
        sources = methodology_data.get('data_sources', [])
        for source in sources:
            self.cell(5, 6, "•", 0, 0, 'L')
            self.cell(185, 6, sanitize_text(source), 0, 1, 'L')
        self.ln(3)
        
        # Assumptions
        if methodology_data.get('assumptions'):
            self.add_subsection_title("4. Key Assumptions")
            for assumption in methodology_data.get('assumptions', []):
                self.cell(5, 6, "•", 0, 0, 'L')
                self.cell(185, 6, sanitize_text(assumption), 0, 1, 'L')
            self.ln(3)
        
        # Limitations
        if methodology_data.get('limitations'):
            self.add_subsection_title("5. Limitations")
            for limitation in methodology_data.get('limitations', []):
                self.cell(5, 6, "•", 0, 0, 'L')
                self.cell(185, 6, sanitize_text(limitation), 0, 1, 'L')
            self.ln(3)
        
        # Compliance statement
        self.add_subsection_title("6. Compliance")
        self.add_paragraph(methodology_data.get('compliance', f'This report complies with {self.report_type} requirements.'))
        self.ln(5)

# ============================================
# ENHANCED REPORT GENERATOR
# ============================================

class EnhancedSustainabilityReportGenerator:
    """Enhanced report generator with automatic narratives and YoY comparison."""
    
    def __init__(self, supabase_client, organization_id, reporting_year, 
                 report_type="SECR", include_narratives=True):
        self.supabase = supabase_client
        self.organization_id = organization_id
        self.reporting_year = reporting_year
        self.report_type = report_type
        self.include_narratives = include_narratives
        
        self.org_data = None
        self.organization_name = None
        self.company_number = None
        
        self.current_year_data = []
        self.previous_year_data = []
        self.scope_totals = {}
        self.previous_scope_totals = {}
        self.total_emissions_tonnes = 0
        self.previous_total_tonnes = 0
        
        self.yoy_comparison = None
        self.emission_sources = []
        self.methodology_notes = []
        self.efficiency_measures = []
        
    def _fetch_organization_data(self):
        """Fetch organization details including metadata for reports."""
        if self.org_data is None:
            # Fetch base organization data
            org_res = self.supabase.from_('organizations')\
                .select('name, company_number, logo_url, industry, sector')\
                .eq('id', self.organization_id)\
                .single()\
                .execute()
            
            if not org_res.data:
                raise HTTPException(status_code=404, detail="Organization not found")
            
            self.org_data = org_res.data
            self.organization_name = sanitize_text(org_res.data.get('name', 'Unknown Organization'))
            self.company_number = sanitize_text(org_res.data.get('company_number', 'N/A'))
            
            # Fetch organization metadata for reporting
            try:
                metadata_res = self.supabase.from_('organization_metadata')\
                    .select('*')\
                    .eq('organization_id', self.organization_id)\
                    .maybe_single()\
                    .execute()
                
                if metadata_res.data:
                    self.org_metadata = metadata_res.data
                    self.total_employees = self.org_metadata.get('total_employees', 0)
                    self.annual_revenue = self.org_metadata.get('annual_revenue', 0)
                    self.total_floor_area = self.org_metadata.get('total_floor_area_sqft', 0)
                    self.renewable_energy_percentage = self.org_metadata.get('renewable_energy_percentage', 0)
                    self.fiscal_year_start = self.org_metadata.get('fiscal_year_start')
                    self.fiscal_year_end = self.org_metadata.get('fiscal_year_end')
                    self.sustainability_officer = self.org_metadata.get('sustainability_officer_name')
                else:
                    # Create default metadata if not exists
                    default_metadata = {
                        'organization_id': self.organization_id,
                        'reporting_standard': 'SECR',
                        'fiscal_year_start': f'{self.reporting_year}-04-01',  # UK tax year starts April
                        'fiscal_year_end': f'{self.reporting_year+1}-03-31',
                        'total_employees': 0,
                        'annual_revenue': 0,
                        'total_floor_area_sqft': 0,
                    }
                    self.supabase.from_('organization_metadata')\
                        .insert(default_metadata)\
                        .execute()
                    
                    self.org_metadata = default_metadata
                    self.total_employees = 0
                    self.annual_revenue = 0
                    self.total_floor_area = 0
                    
            except Exception as e:
                print(f"⚠️ Error fetching organization metadata: {e}")
                self.org_metadata = {}
                self.total_employees = 0
                self.annual_revenue = 0
                self.total_floor_area = 0
        
        return self.org_data

    def _fetch_emissions_data(self, year=None):
        """Fetch emissions data with pagination."""
        if year is None:
            year = self.reporting_year
            
        all_data = []
        has_more = True
        page = 0
        page_size = 1000
        
        while has_more:
            start = page * page_size
            end = (page + 1) * page_size - 1
            
            response = self.supabase.from_('emissions_logs')\
                .select('*, defra_conversion_factors(activity_type, co2e_multiplier, reporting_year), assets(name, facilities(name))')\
                .eq('organization_id', self.organization_id)\
                .gte('start_date', f'{year}-01-01')\
                .lte('start_date', f'{year}-12-31')\
                .range(start, end)\
                .execute()
                
            data = response.data or []
            if data:
                all_data.extend(data)
                page += 1
            if len(data) < page_size:
                has_more = False
        
        return all_data
    
    def _calculate_scope_totals(self, emissions_data):
        """Calculate scope totals from emissions data."""
        scope_totals = {'Scope 1': 0, 'Scope 2': 0, 'Scope 3': 0}
        total_emissions = 0
        
        for record in emissions_data:
            kg_co2e = float(record.get('calculated_kg_co2e', 0))
            total_emissions += kg_co2e
            
            metadata = record.get('metadata', {}) or {}
            defra = record.get('defra_conversion_factors', {}) or {}
            
            scope = metadata.get('scope', 'Unknown')
            if scope == 'Unknown':
                activity = defra.get('activity_type', '')
                if any(f in activity for f in ['Diesel', 'Petrol', 'Natural Gas', 'LPG']):
                    scope = 'Scope 1'
                elif 'Electricity' in activity:
                    scope = 'Scope 2'
                else:
                    scope = 'Scope 3'
                    
            if scope in scope_totals:
                scope_totals[scope] += kg_co2e
            else:
                scope_totals['Scope 3'] += kg_co2e
                
        return scope_totals, total_emissions
    
    def _calculate_yoy_comparison(self) -> YearOverYearComparison:
        """Calculate year-over-year comparison."""
        current_year_kg = sum(r.get('calculated_kg_co2e', 0) for r in self.current_year_data)
        previous_year_kg = sum(r.get('calculated_kg_co2e', 0) for r in self.previous_year_data)
        
        current_tonnes = current_year_kg / 1000
        previous_tonnes = previous_year_kg / 1000
        
        absolute_change = current_tonnes - previous_tonnes
        percentage_change = 0
        if previous_tonnes > 0:
            percentage_change = (absolute_change / previous_tonnes) * 100
        
        if percentage_change < -10:
            trend = "decrease"
            narrative = f"Significant decrease of {abs(percentage_change):.1f}% in emissions compared to previous year."
        elif percentage_change < -2:
            trend = "decrease"
            narrative = f"Moderate decrease of {abs(percentage_change):.1f}% in emissions compared to previous year."
        elif percentage_change < 2:
            trend = "stable"
            narrative = f"Stable emissions with minimal change of {abs(percentage_change):.1f}% compared to previous year."
        elif percentage_change < 10:
            trend = "increase"
            narrative = f"Moderate increase of {percentage_change:.1f}% in emissions compared to previous year."
        else:
            trend = "increase"
            narrative = f"Significant increase of {percentage_change:.1f}% in emissions compared to previous year."
        
        return YearOverYearComparison(
            current_year=self.reporting_year,
            previous_year=self.reporting_year - 1,
            current_emissions=current_tonnes,
            previous_emissions=previous_tonnes,
            absolute_change=absolute_change,
            percentage_change=percentage_change,
            trend_direction=trend,
            narrative=narrative
        )
    
    def _generate_methodology_notes(self) -> List[MethodologyNote]:
        """Generate comprehensive methodology notes."""
        notes = []
        
        # Overview
        notes.append(MethodologyNote(
            section="overview",
            title="Methodology Overview",
            description=f"Emissions for {self.organization_name} have been calculated using standard GHG Protocol methodologies.",
            data_sources=["Utility bills", "Fuel consumption records", "Asset operational data"],
            calculation_method="DEFRA conversion factors applied to consumption data",
            assumptions=["Consumption data is accurate", "Factors reflect current reporting year"],
            limitations=["Limited to available data", "Some estimates may be used"]
        ))
        
        # Scope specific notes
        for scope in ['Scope 1', 'Scope 2', 'Scope 3']:
            if self.scope_totals.get(scope, 0) > 0:
                notes.append(MethodologyNote(
                    section=scope.lower().replace(' ', '_'),
                    title=f"{scope} Calculation Method",
                    description=f"{scope} emissions calculated from direct measurements and standard factors.",
                    data_sources=[f"{scope} activity data from operational records"],
                    calculation_method=f"Sum of activity data × emission factors",
                    assumptions=[f"{scope} data represents full year operations"],
                    limitations=[f"{scope} calculations are based on available data"]
                ))
        
        return notes
    
    def _generate_efficiency_measures(self) -> List[EfficiencyMeasure]:
        """Generate energy efficiency measures from data analysis."""
        measures = []
        
        # Analyze data to identify efficiency opportunities
        total_kg = sum(r.get('calculated_kg_co2e', 0) for r in self.current_year_data)
        
        if total_kg > 100000:  # More than 100 tonnes CO2e
            measures.append(EfficiencyMeasure(
                name="Energy Efficiency Program",
                category="Energy",
                description="Implement comprehensive energy efficiency measures across facilities.",
                estimated_savings_tonnes=total_kg / 1000 * 0.15,  # 15% potential savings
                implementation_status="planned"
            ))
        
        # Check for renewable energy opportunities
        scope2 = self.scope_totals.get('Scope 2', 0)
        if scope2 > 50000:  # More than 50 tonnes CO2e from Scope 2
            measures.append(EfficiencyMeasure(
                name="Renewable Energy Transition",
                category="Renewables",
                description="Transition to renewable energy sources for electricity consumption.",
                estimated_savings_tonnes=scope2 / 1000 * 0.8,  # 80% potential reduction
                implementation_status="in_progress"
            ))
        
        # Check for fleet efficiency
        scope1 = self.scope_totals.get('Scope 1', 0)
        if scope1 > 100000:
            measures.append(EfficiencyMeasure(
                name="Fleet Electrification",
                category="Transportation",
                description="Replace combustion engine vehicles with electric alternatives.",
                estimated_savings_tonnes=scope1 / 1000 * 0.3,  # 30% potential reduction
                implementation_status="planned"
            ))
        
        return measures
    
    def _generate_emission_sources(self) -> List[EmissionSource]:
        """Generate emission source breakdown."""
        sources = []
        total_kg = sum(r.get('calculated_kg_co2e', 0) for r in self.current_year_data)
        
        # Group by activity type
        activity_groups = {}
        for record in self.current_year_data:
            defra = record.get('defra_conversion_factors', {})
            activity = defra.get('activity_type', 'Unknown')
            kg = record.get('calculated_kg_co2e', 0)
            
            if activity not in activity_groups:
                activity_groups[activity] = {
                    'total_kg': 0,
                    'count': 0,
                    'scope': 'Unknown',
                    'asset': None,
                    'facility': None
                }
            
            activity_groups[activity]['total_kg'] += kg
            activity_groups[activity]['count'] += 1
            
            # Determine scope
            metadata = record.get('metadata', {})
            scope = metadata.get('scope', 'Unknown')
            if scope == 'Unknown':
                if any(f in activity for f in ['Diesel', 'Petrol', 'Natural Gas', 'LPG']):
                    scope = 'Scope 1'
                elif 'Electricity' in activity:
                    scope = 'Scope 2'
                else:
                    scope = 'Scope 3'
            activity_groups[activity]['scope'] = scope
            
            # Get asset info
            asset = record.get('assets', {})
            if asset and not activity_groups[activity]['asset']:
                activity_groups[activity]['asset'] = asset.get('name')
                facility = asset.get('facilities', {})
                activity_groups[activity]['facility'] = facility.get('name')
        
        # Convert to EmissionSource objects
        for activity, data in activity_groups.items():
            kg = data['total_kg']
            percentage = (kg / total_kg * 100) if total_kg > 0 else 0
            
            sources.append(EmissionSource(
                activity_type=activity,
                scope=data['scope'],
                quantity=data['count'],
                unit='records',
                kg_co2e=kg,
                tonnes_co2e=kg / 1000,
                percentage=percentage,
                asset_name=data['asset'],
                facility_name=data['facility']
            ))
        
        # Sort by emissions (highest first)
        sources.sort(key=lambda x: x.kg_co2e, reverse=True)
        return sources
    
    def _generate_report_highlights(self) -> Dict:
        """Generate report highlights for cover page."""
        # Calculate intensity ratios using the helper function
        intensity_ratios = calculate_intensity_ratios(
            self.total_emissions_tonnes,
            self.org_metadata or {}
        )
        
        return {
            'metrics': {
                'total_tonnes': self.total_emissions_tonnes,
                'scope1': self.scope_totals.get('Scope 1', 0) / 1000,
                'scope2': self.scope_totals.get('Scope 2', 0) / 1000,
                'scope3': self.scope_totals.get('Scope 3', 0) / 1000,
                'records': len(self.current_year_data),
                'yoy_change': self.yoy_comparison.percentage_change if self.yoy_comparison else 0
            },
            'intensity_ratios': intensity_ratios  # ✅ Add this
        }

    
    def generate_enhanced_secr_report(self) -> Dict:
        """Generate enhanced SECR report with all features."""
        self._fetch_organization_data()
        
        # Fetch data
        self.current_year_data = self._fetch_emissions_data(self.reporting_year)
        self.previous_year_data = self._fetch_emissions_data(self.reporting_year - 1)
        
        if not self.current_year_data:
            raise HTTPException(status_code=404, detail="No emissions data found for this organization.")
        
        # Calculate metrics
        self.scope_totals, total_kg = self._calculate_scope_totals(self.current_year_data)
        self.total_emissions_tonnes = total_kg / 1000
        
        if self.previous_year_data:
            self.previous_scope_totals, prev_total_kg = self._calculate_scope_totals(self.previous_year_data)
            self.previous_total_tonnes = prev_total_kg / 1000
        
        # Generate narratives
        self.yoy_comparison = self._calculate_yoy_comparison()
        self.emission_sources = self._generate_emission_sources()
        self.methodology_notes = self._generate_methodology_notes()
        self.efficiency_measures = self._generate_efficiency_measures()
        
        # Create PDF
        pdf = EnhancedSustainabilityReportPDF(
            self.organization_name, 
            self.reporting_year, 
            "SECR",
            theme_color=(22, 163, 74)
        )
        
        # Generate report pages
        self._generate_enhanced_pdf(pdf)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        return {
            "status": "success",
            "report_type": "SECR",
            "pdf_base64": base64.b64encode(pdf_output).decode('utf-8'),
            "filename": f"SECR_Report_{self.organization_name}_{self.reporting_year}.pdf",
            "metadata": {
                "total_emissions_tonnes": self.total_emissions_tonnes,
                "records_used": len(self.current_year_data),
                "yoy_change": self.yoy_comparison.percentage_change if self.yoy_comparison else 0,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def _generate_enhanced_pdf(self, pdf):
        """Generate the complete enhanced PDF report."""
        # Cover page
        pdf.add_cover_page(self._generate_report_highlights())
        
        # Table of Contents (placeholder)
        pdf.add_page()
        pdf.add_section_title("📑 Table of Contents")
        toc_items = [
            ("1. Executive Summary", 1),
            ("2. Emissions Overview", 2),
            ("3. Year-over-Year Comparison", 3),
            ("4. Emissions Breakdown", 4),
            ("5. Methodology", 5),
            ("6. Energy Efficiency Measures", 6),
            ("7. Compliance Statement", 7)
        ]
        for item, level in toc_items:
            pdf.set_font('Helvetica', 'B' if level == 1 else '', 11)
            pdf.cell(10, 8, f"{level}.", 0, 0, 'L')
            pdf.cell(140, 8, sanitize_text(item), 0, 0, 'L')
            pdf.cell(40, 8, f"Page {level + 1}", 0, 1, 'R')
        pdf.ln(10)
        
        # 1. Executive Summary
        pdf.add_page()
        pdf.add_section_title("1. Executive Summary")
        
        # Summary text
        summary_text = f"""
        {self.organization_name} has completed its sustainability reporting for the financial year {self.reporting_year}. 
        Total emissions for the reporting period were {self.total_emissions_tonnes:,.0f} tonnes CO2e.
        """
        if self.yoy_comparison:
            summary_text += f" This represents a {self.yoy_comparison.percentage_change:+.1f}% change from the previous year."
        pdf.add_paragraph(summary_text)
        pdf.ln(5)
        
        # Key metrics
        pdf.add_subsection_title("Key Metrics")
        metrics = [
            ("Total Emissions", f"{self.total_emissions_tonnes:,.0f}", "tonnes CO2e"),
            ("Scope 1", f"{self.scope_totals.get('Scope 1', 0)/1000:,.0f}", "tonnes CO2e"),
            ("Scope 2", f"{self.scope_totals.get('Scope 2', 0)/1000:,.0f}", "tonnes CO2e"),
            ("Scope 3", f"{self.scope_totals.get('Scope 3', 0)/1000:,.0f}", "tonnes CO2e"),
            ("Total Records", f"{len(self.current_year_data)}", "records"),
        ]
        for label, value, unit in metrics:
            pdf.add_metric_box(label, value, unit)
        pdf.ln(5)
        
        # YoY Trend
        if self.yoy_comparison:
            pdf.add_trend_indicator(self.yoy_comparison.percentage_change)
            pdf.add_paragraph(self.yoy_comparison.narrative)
        
        # 2. Emissions Overview
        pdf.add_page()
        pdf.add_section_title("2. Emissions Overview")
        
        # Emissions by scope table
        scope_data = [
            ['Scope 1', f"{self.scope_totals.get('Scope 1', 0)/1000:,.2f}", f"{(self.scope_totals.get('Scope 1', 0)/1000/self.total_emissions_tonnes*100):.1f}%"],
            ['Scope 2', f"{self.scope_totals.get('Scope 2', 0)/1000:,.2f}", f"{(self.scope_totals.get('Scope 2', 0)/1000/self.total_emissions_tonnes*100):.1f}%"],
            ['Scope 3', f"{self.scope_totals.get('Scope 3', 0)/1000:,.2f}", f"{(self.scope_totals.get('Scope 3', 0)/1000/self.total_emissions_tonnes*100):.1f}%"],
        ]
        pdf.add_data_table(['Scope', 'Emissions (tonnes CO2e)', 'Percentage'], scope_data, highlight_best=True)
        pdf.ln(10)
        
        # 3. Year-over-Year Comparison
        if self.yoy_comparison:
            pdf.add_page()
            pdf.add_section_title("3. Year-over-Year Comparison")
            
            yoy_data = [
                ['Metric', f'{self.yoy_comparison.previous_year}', f'{self.yoy_comparison.current_year}', 'Change'],
                ['Total Emissions (tonnes CO2e)', f"{self.yoy_comparison.previous_emissions:,.2f}", f"{self.yoy_comparison.current_emissions:,.2f}", f"{self.yoy_comparison.absolute_change:+.2f}"],
            ]
            pdf.add_data_table(['Metric', 'Previous Year', 'Current Year', 'Change'], yoy_data)
            pdf.ln(10)
            
            # Narrative
            pdf.add_narrative_box(
                "Analysis",
                f"{self.yoy_comparison.narrative} The absolute change is {abs(self.yoy_comparison.absolute_change):,.2f} tonnes CO2e.",
                "comparison"
            )
        
        # 4. Methodology
        pdf.add_page()
        pdf.add_section_title("4. Methodology")
        
        for note in self.methodology_notes[:1]:  # Show first methodology note
            pdf.add_subsection_title(note.title)
            pdf.add_paragraph(note.description)
            pdf.add_paragraph(f"Data Sources: {', '.join(note.data_sources)}")
            pdf.add_paragraph(f"Calculation Method: {note.calculation_method}")
            pdf.ln(3)
        
        # 5. Energy Efficiency Measures
        if self.efficiency_measures:
            pdf.add_page()
            pdf.add_section_title("5. Energy Efficiency Measures")
            
            for measure in self.efficiency_measures:
                pdf.add_subsection_title(measure.name)
                pdf.add_paragraph(f"Category: {measure.category}")
                pdf.add_paragraph(f"Description: {measure.description}")
                pdf.add_paragraph(f"Estimated Savings: {measure.estimated_savings_tonnes:,.2f} tonnes CO2e")
                pdf.add_paragraph(f"Status: {measure.implementation_status.replace('_', ' ').title()}")
                pdf.ln(3)
        
        # 6. Compliance Statement
        pdf.add_page()
        pdf.add_section_title("6. Compliance Statement")
        
        compliance_text = f"""
        This report has been prepared in accordance with the Streamlined Energy and Carbon Reporting (SECR) regulations 
        under the Companies (Directors Report) and Limited Liability Partnerships (Energy and Carbon Report) Regulations 2018.
        
        All emissions have been calculated using UK Government GHG Conversion Factors for Company Reporting ({self.reporting_year}).
        
        This report provides a true and fair view of {self.organization_name}'s greenhouse gas emissions for the reporting period.
        """
        pdf.add_paragraph(compliance_text)
        pdf.ln(10)
        
        # Signature block
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 8, "Signed on behalf of the Board:", 0, 1, 'L')
        pdf.ln(10)
        pdf.cell(80, 8, "_______________________", 0, 0, 'L')
        pdf.cell(30, 8, "", 0, 0, 'L')
        pdf.cell(80, 8, "_______________________", 0, 1, 'L')
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(80, 6, "Director", 0, 0, 'C')
        pdf.cell(30, 6, "", 0, 0, 'L')
        pdf.cell(80, 6, "Date", 0, 1, 'C')

# ============================================
# API ENDPOINT
# ============================================

class EnhancedReportRequest(BaseModel):
    organization_id: str
    reporting_year: int
    report_type: str = "SECR"  # SECR, CSRD, ISSB
    include_narratives: bool = True

@router.post("/generate-enhanced-report")
async def generate_enhanced_sustainability_report(request: EnhancedReportRequest):
    """Generate an enhanced sustainability report with narratives and YoY comparison."""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        generator = EnhancedSustainabilityReportGenerator(
            supabase_client, 
            request.organization_id, 
            request.reporting_year,
            request.report_type,
            request.include_narratives
        )
        
        if request.report_type == 'SECR':
            result = generator.generate_enhanced_secr_report()
        elif request.report_type == 'CSRD':
            # You can add enhanced CSRD report generation here
            result = generator.generate_enhanced_secr_report()  # Placeholder
        elif request.report_type == 'ISSB':
            # You can add enhanced ISSB report generation here
            result = generator.generate_enhanced_secr_report()  # Placeholder
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"--- ENHANCED REPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")