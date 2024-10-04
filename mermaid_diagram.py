import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("No API key found. Please make sure GOOGLE_API_KEY is set in your .env file.")
    st.stop()

genai.configure(api_key=api_key)

def get_gemini_response(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]

        response = model.generate_content(
            prompt,
            safety_settings=safety_settings,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        return response.text
    except Exception as e:
        st.error(f"Error in get_gemini_response: {e}")
        return None

def clean_mermaid_code(mermaid_code):
    # Remove any markdown code blocks
    cleaned_code = mermaid_code.replace('```mermaid', '').replace('```', '').strip()
    
    # Remove multiple graph definitions, keep only 'graph TD'
    graph_types = ['graph TD', 'graph LR', 'graph TB', 'graph BT', 'graph RL']
    for graph_type in graph_types:
        if graph_type in cleaned_code and graph_type != 'graph TD':
            cleaned_code = cleaned_code.replace(graph_type, '')
    
    # Ensure the code starts with 'graph TD'
    if not cleaned_code.startswith('graph TD'):
        cleaned_code = 'graph TD\n' + cleaned_code
    
    # Fix subgraph syntax if present
    if 'subgraph' in cleaned_code:
        lines = cleaned_code.split('\n')
        fixed_lines = []
        for line in lines:
            if 'subgraph' in line and ']' not in line:
                # Add missing bracket for subgraph title
                line = line.replace('subgraph', 'subgraph ') + ' ['
            fixed_lines.append(line)
        cleaned_code = '\n'.join(fixed_lines)
    
    # Remove any empty lines
    cleaned_code = '\n'.join(line for line in cleaned_code.split('\n') if line.strip())
    
    return cleaned_code

def generate_mermaid(description):
    prompt = f"""Generate a Mermaid diagram code for a workflow based on the following description:

Description: {description}

Please provide only the Mermaid code that represents this workflow. Use 'graph TD' for a top-down flowchart. Do not use subgraphs unless specifically requested. Keep the syntax simple and focus on showing the flow between steps.

Mermaid code:"""

    mermaid_code = get_gemini_response(prompt)
    
    if mermaid_code:
        return clean_mermaid_code(mermaid_code)
    return None

def render_mermaid(mermaid_code):
    html = f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/9.3.0/mermaid.min.js"></script>
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%; position: relative;">
            <div id="mermaid-diagram" style="width: 100%; background-color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; overflow: auto; max-height: 600px;">
                <pre class="mermaid" style="margin: 0;">
                    {mermaid_code}
                </pre>
            </div>
            <div onclick="downloadSVG()" style="position: absolute; top: 10px; right: 10px; cursor: pointer; background-color: white; border-radius: 50%; padding: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
            </div>
        </div>
        <div id="error-message" style="color: red; display: none;"></div>
        
        <script>
            try {{
                mermaid.initialize({{
                    startOnLoad: true,
                    securityLevel: 'loose',
                    theme: 'default',
                    maxTextSize: 900,
                    logLevel: 'error',
                }});
                
                function renderDiagram() {{
                    try {{
                        mermaid.init(undefined, document.querySelector('.mermaid'));
                        
                        // Make SVG responsive and centered
                        var svg = document.querySelector('.mermaid svg');
                        if (svg) {{
                            svg.style.width = '50%';  
                            svg.style.height = 'auto';
                            svg.style.maxWidth = '100%';
                            svg.style.display = 'block';
                            svg.style.margin = 'auto';
                            
                            // Get the viewBox values
                            var viewBox = svg.getAttribute('viewBox');
                            
                            if (viewBox) {{
                                var viewBoxValues = viewBox.split(' ').map(Number);
                                if (viewBoxValues.length === 4) {{
                                    var vbWidth = viewBoxValues[2];
                                    var vbHeight = viewBoxValues[3];
                                    
                                    // Calculate scaling factor
                                    var containerWidth = svg.clientWidth;
                                    var scaleFactor = containerWidth / vbWidth;
                                    
                                    // Apply scaling transform
                                    svg.style.transform = 'scale(' + scaleFactor + ')';
                                    svg.style.transformOrigin = 'top center';
                                    
                                    // Set container height
                                    var containerHeight = vbHeight * scaleFactor;
                                    svg.style.height = containerHeight + 'px';
                                }}
                            }}
                        }}
                    }} catch (err) {{
                        console.error('Mermaid rendering error:', err);
                        document.getElementById('error-message').style.display = 'block';
                        document.getElementById('error-message').textContent = 
                            'Diagram rendering failed: ' + err.message;
                    }}
                }}

                function downloadSVG() {{
                    var svg = document.querySelector('.mermaid svg');
                    if (svg) {{
                        var svgData = svg.outerHTML;
                        var svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                        var svgUrl = URL.createObjectURL(svgBlob);
                        var downloadLink = document.createElement('a');
                        downloadLink.href = svgUrl;
                        downloadLink.download = 'workflow_diagram.svg';
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        document.body.removeChild(downloadLink);
                        URL.revokeObjectURL(svgUrl);
                    }}
                }}

                // Increase timeout to ensure the diagram is rendered
                setTimeout(renderDiagram, 500);
                
            }} catch (err) {{
                console.error('Mermaid initialization error:', err);
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = 
                    'Failed to initialize Mermaid: ' + err.message;
            }}
        </script>
    """
    # Increase height to accommodate larger diagrams
    return components.html(html, height=800)

def render_example(title, description, mermaid_code):
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button(f"View: {title}", key=f"btn_{title}"):
            st.session_state[f"show_{title}"] = not st.session_state.get(f"show_{title}", False)
    
    with col2:
        st.markdown(f"**{title}**: {description}")
    
    if st.session_state.get(f"show_{title}", False):
        st.code(mermaid_code, language="mermaid")
        render_mermaid(mermaid_code)

# Main app
st.title("Workflow Diagram Generator ✦")

user_input = st.text_area("Describe your workflow process:", height=150)

if st.button("Generate Diagram"):
    if user_input:
        try:
            with st.spinner("🤖 AI is thinking... Please wait..."):
                mermaid_code = generate_mermaid(user_input)
            
            if mermaid_code:
                st.subheader("Your Workflow Diagram:")
                render_mermaid(mermaid_code)
                
                # Move this after the diagram
                st.code(mermaid_code, language="mermaid")
            else:
                st.error("Failed to generate Mermaid code. Please try again.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a workflow process description.")

# Example Workflow Diagrams Section
st.markdown("""
------------------------
#### 👉 Example: 

"Code commit triggers build process, runs unit tests, if tests pass then deploy to staging environment, run integration tests, if all tests pass then deploy to production, monitor application performance"
""")

st.markdown("""
----------------
### 💁🏻 Example Workflow Diagrams

✦ Click on an example to view its diagram:
""")

# Define your examples
examples = [
    {
        "title": "Simple Linear Workflow",
        "description": "A basic linear workflow with a clear sequence of tasks.",
        "code": """
graph TD
    A[Start] --> B[Task 1]
    B --> C[Task 2]
    C --> D[Task 3]
    D --> E[End]
"""
    },
    {
        "title": "Branching Workflow",
        "description": "A workflow with a decision point leading to different paths.",
        "code": """
graph TD
    A[Start] --> B{Decision}
    B -->|Option 1| C[Task 1]
    B -->|Option 2| D[Task 2]
    C --> E[End]
    D --> E
"""
    },
    {
        "title": "Parallel Tasks Workflow",
        "description": "A workflow where multiple tasks are performed concurrently.",
        "code": """
graph TD
    A[Start] --> B[Task 1]
    A --> C[Task 2]
    A --> D[Task 3]
    B --> E[Combine Results]
    C --> E
    D --> E
    E --> F[End]
"""
    },
    {
        "title": "Complex SD Workflow",
        "description": "A more detailed workflow representing a software development and deployment process.",
        "code": """
graph TD
    A[Code Commit] --> B[Build]
    B --> C{Unit Tests}
    C -->|Pass| D[Deploy to Staging]
    C -->|Fail| E[Notify Developer]
    E --> A
    D --> F{Integration Tests}
    F -->|Pass| G[Deploy to Production]
    F -->|Fail| H[Rollback & Notify]
    H --> A
    G --> I[Monitor Application]
    I --> J{Performance OK?}
    J -->|Yes| K[Continue]
    J -->|No| L[Investigate & Fix]
    L --> A
"""
    }
]

# Render all examples
for example in examples:
    render_example(example["title"], example["description"], example["code"])

st.markdown("""
            
👉 These examples demonstrate various ways to structure workflow diagrams using Mermaid. You can use these as starting points and modify them to fit your specific needs.

""")

st.markdown("""
            ----------------------------------------------------
### 💡Tips for best results:
1. Be clear and specific in your workflow description
2. Include key steps, decision points, and connections between elements
3. Mention any parallel processes or conditions if applicable
4. If the generated diagram isn't perfect, you can always edit the code manually

""")


st.markdown("""
---
<div style="text-align: center;">
    Built with ❤️ by <a href="https://www.linkedin.com/in/gitesh-mahadik-7487961a0/" target="_blank">Gitesh</a>
</div>
""", unsafe_allow_html=True)
