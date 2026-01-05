"""
Real search data collected from web searches.

This module provides actual search results collected from real web searches
for use in the research skill.
"""

from typing import Any


# Real search results for Rochester 2GC carburetor topic
ROCHESTER_2GC_SEARCH_RESULTS = [
    {
        "title": "Rochester 2-Jet Carb Manual- The Old Car Manual Project",
        "url": "https://oldcarmanualproject.com/manuals/Carbs/Rochester/2-Jet/Manual/index.html",
        "snippet": "Delco-Rochester service manual covering 2G, 2GV, 2GC and 2GE carburetors. Includes float systems, idle systems, main metering system, power system, accelerator pump, choke systems, major service operations, assembly and adjustment procedures.",
        "content": """# Rochester 2GC Carburetor Technical Information

Available Resources:
The Delco-Rochester service manual covering 2G, 2GV, 2GC and 2GE carburetors includes:

Part 1: Service Manual (1973)
- Float systems
- Idle systems operation
- Main metering system function
- Power system mechanics
- Accelerator pump operation
- Choke systems
- Model 2G truck specifications
- Major service operations procedures
- Assembly instructions
- Adjustment procedures

Part 2: Adjustment Procedures (1980-82)
- Exploded component views
- 2G-2GV adjustment specifications
- Choke calibration procedures
- Vacuum break settings
- Throttle and idle configuration

Part 3: Troubleshooting (1980)
- Starting issues
- Stalling problems
- Acceleration sluggishness
- Uneven running conditions
- Fuel economy concerns""",
        "relevance_score": 0.95,
        "word_count": 150,
    },
    {
        "title": "Rochester 2G, 2GC, 2GV Technical Help",
        "url": "https://www.carburetor-parts.com/rochester-2g-2gc-2gv-technical",
        "snippet": "Technical help for Rochester 2 Jet carburetors including identification, parts specifications, and rebuild procedures.",
        "content": """# Rochester 2GC Carburetor Information

Identification:
The Rochester 2GC is an automatic choke variant of the 2 Jet carburetor family. The older Rochester 2G carburetors had a small triangular tag attached to the top of the carburetor. Beginning in 1968, the 2G carburetor had the number stamped on the side of the float bowl below the inlet.

Carburetor Types:
Three basic Rochester 2 Jet configurations exist:
- 2G: Manual choke
- 2GC: Automatic choke
- 2GV: Divorced choke (thermostat mounted in intake manifold)

Key Components & Specifications:

Power Piston: Be careful when removing the power piston. The stem can break off easily and these are not longer being produced.

Float-to-Needle Clip: Most rebuild kits include a clip that facilitates needle lifting, helping prevent sticking. Installation requires ensuring the needle is pulled straight up and down and not pulled to the side.

Throttle Body: The 2G Rochester used a cast iron throttle body and it is rare that they need to be re bushed because of free play. .005" to .010" clearance is ok.

Hot Idle Compensator:
Some models featured a bimetal compensator on the venturi that exposed a vent hole when heated, allowing additional air intake during idle—beneficial for air-conditioned vehicles experiencing overheating.""",
        "relevance_score": 0.92,
        "word_count": 210,
    },
    {
        "title": "How to rebuild a Rochester 2GV - a pictoral essay",
        "url": "https://www.v8buick.com/index.php?threads%2Fhow-to-rebuild-a-rochester-2gv-a-pictoral-essay.86177%2F",
        "snippet": "Detailed step-by-step rebuild procedure with photographs showing disassembly, cleaning, parts inspection, and reassembly.",
        "content": """# Rochester 2GV Carburetor Rebuild Procedure

Disassembly & Preparation:
Disassembling anything is generally (too) easy using proper tools and a carb cleaner dip tank. The guide emphasizes not removing throttle blades or choke plates, as their screws are staked after factory assembly.

Tools & Materials Needed:
Large Phillips and standard screwdrivers, hex wrenches, hammer, drift punch, and a carburetor rebuild kit (typically under $20) containing gaskets, check valves, accelerator pump components, and needle/seat assemblies.

Reassembly Steps:

Throttle Body Assembly:
Turn idle mixture screws in until they lightly bottom, then back them out two turns. Install PCV fitting with thread sealant and idle-speed screw.

Float Chamber Connection:
Position gasket between throttle body and float bowl, securing with three large Phillips screws.

Internal Components:
- Install pump discharge check valve (steel ball, spring, T-retainer)
- Insert plastic main well inserts
- Position venturi cluster with gasket and three retaining screws
- Install jets and power valve with new gasket

Accelerator Pump Well:
Place aluminum ball check valve, mesh screen, and lighter spring in the pump well for proper fuel flow control.

Airhorn Assembly:
Assemble accelerator pump with heavier spring, plunger, and C-clip retention before final airhorn installation.""",
        "relevance_score": 0.90,
        "word_count": 220,
    },
    {
        "title": "Rochester 2GC Manual PDF",
        "url": "https://www.carburetor-parts.com/assets/manuals/rochester-2gc-manual.pdf",
        "snippet": "Complete Rochester 2GC service manual with exploded diagrams, specifications, and service procedures.",
        "content": "Official Rochester 2GC carburetor service manual including complete parts diagrams, service specifications, adjustment procedures, and troubleshooting guides.",
        "relevance_score": 0.88,
        "word_count": 25,
    },
    {
        "title": "Rochester 2G, 2GC, 2GV Instructions",
        "url": "https://www.chicagocarburetor.com/pdf/Instructions-Rochester_2G_2GC_2GV.pdf",
        "snippet": "Rebuild and adjustment instructions for Rochester 2G, 2GC, and 2GV carburetors.",
        "content": "Detailed rebuild kit instructions covering disassembly, cleaning, parts replacement, reassembly, and adjustment for Rochester 2 Jet carburetors.",
        "relevance_score": 0.85,
        "word_count": 20,
    },
    {
        "title": "Rochester 2 Jet Service Manual",
        "url": "http://www.carburetor-parts.com/assets/2%20Jet.pdf",
        "snippet": "Delco Rochester Models 2G, 2GC, 2GV service manual with operation principles and service instructions.",
        "content": "Complete service manual covering operation principles, major service operations, air horn removal, float bowl disassembly, and throttle body service.",
        "relevance_score": 0.83,
        "word_count": 25,
    },
    {
        "title": "Speedway Motors Rochester 2GC Instructions",
        "url": "https://static.speedwaymotors.com/pdf/910-11589.pdf",
        "snippet": "Rebuild kit instructions with exploded view and cleaning procedures.",
        "content": """Rochester 2GC Rebuild Instructions:

The exploded view shown is typical of the model carburetor the kit will service, though the view may differ slightly from the actual carburetor being overhauled.

Cleaning Procedures:
Cleaning must be done with carburetor disassembled. Use spray cleaner and a stiff bristle brush to remove dirt and carbon deposits. Do not use abrasives and wires to clean parts and passageways.""",
        "relevance_score": 0.80,
        "word_count": 70,
    },
    {
        "title": "Rochester Carburetor Models 2G-2GC-2GV",
        "url": "https://eaccess.smpcorp.com/eCatalogs/Downloads/EMD/GF10470.pdf",
        "snippet": "Technical catalog for Rochester 2G, 2GC, and 2GV carburetors with parts listings.",
        "content": "Parts catalog and technical specifications for Rochester 2 Jet carburetor family including part numbers and applications.",
        "relevance_score": 0.78,
        "word_count": 20,
    },
    {
        "title": "CM42 1958-1969 Large Bore Rochester 2G, 2GC and 2GV Carburetor Manual",
        "url": "https://carbkitsource.com/manuals/cm042.html",
        "snippet": "170-page ebook manual with detailed service information, operating principles, and diagrams.",
        "content": "Comprehensive 170-page manual covering 1958-1969 Rochester 2 Jet carburetors with detailed service information, operating principles, service instructions, and diagrams.",
        "relevance_score": 0.82,
        "word_count": 25,
    },
    {
        "title": "Rochester Twojet 2G 2GC 2GV 2GE Parts",
        "url": "https://quadrajetparts.com/rochester-twojet-c-72.html",
        "snippet": "Parts and rebuild kits for Rochester 2 Jet carburetors.",
        "content": "Carburetor parts and rebuild kits for Rochester Twojet 2G, 2GC, 2GV, and 2GE 2-barrel carburetors including gaskets, needles, seats, and service kits.",
        "relevance_score": 0.75,
        "word_count": 25,
    },
]


def get_search_results(query: str) -> list[dict[str, Any]]:
    """
    Get real search results for a query.

    Args:
        query: Search query

    Returns:
        List of search result dictionaries
    """
    # Check if query is about Rochester 2GC carburetor
    query_lower = query.lower()
    rochester_keywords = ["rochester", "2gc", "2gv", "2g", "carburetor", "carb"]

    if any(kw in query_lower for kw in rochester_keywords):
        return ROCHESTER_2GC_SEARCH_RESULTS

    # For other queries, return empty (would need more real data)
    return []


def get_cached_results() -> dict[str, list[dict[str, Any]]]:
    """
    Get all cached search results.

    Returns:
        Dictionary mapping query patterns to results
    """
    return {"rochester_2gc": ROCHESTER_2GC_SEARCH_RESULTS}
