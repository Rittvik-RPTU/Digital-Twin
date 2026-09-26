#!/usr/bin/env python3
"""
Generate streamlined, high-contrast Draw.io (.drawio) XML diagram files for Chapter 3:
1. threat_mitigation_pipeline.drawio: Cascading Security Pipeline & Threat Mitigation Architecture
2. hybrid_defense_concept.drawio: Dual-Layer Telemetry Validation Architecture (Hard vs. Soft Bounds)

Features:
- High contrast dark text (#0F172A, #1E293B, #991B1B, etc.) on all white/light backgrounds.
- Distinct non-overlapping arrow paths with dedicated vertical/horizontal corridors.
- Clean typography and professional palette.
"""

import os

def create_threat_mitigation_drawio():
    xml = '''<mxfile host="app.diagrams.net" agent="Antigravity AI" version="24.7.5">
  <diagram id="threat-mitigation-pipeline" name="Threat Mitigation Pipeline">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1420" pageHeight="800" background="#F8FAFC" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Canvas Header -->
        <mxCell id="canvas_title" parent="1" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=20;fontStyle=1;fontColor=#0F172A;" value="Cascading Security Pipeline &amp; Threat Mitigation Architecture" vertex="1">
          <mxGeometry x="100" y="15" width="1220" height="35" as="geometry" />
        </mxCell>
        <mxCell id="canvas_subtitle" parent="1" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=13;fontStyle=2;fontColor=#334155;" value="Systematic Defense-in-Depth Across Four Cascading Enforcement Stages" vertex="1">
          <mxGeometry x="100" y="45" width="1220" height="25" as="geometry" />
        </mxCell>

        <!-- ==================== TOP ROW: INGRESS & ADVERSARIES ==================== -->
        <!-- Valid Ingress -->
        <mxCell id="node_legit" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 13px; color: #14532D;&quot;&gt;Valid Client&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Authenticated PT / User&lt;br/&gt;&amp;bull; Standard Telemetry&lt;/font&gt;" vertex="1">
          <mxGeometry x="40" y="90" width="180" height="100" as="geometry" />
        </mxCell>

        <!-- A_ext -->
        <mxCell id="node_a_ext" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 13px; color: #991B1B;&quot;&gt;A_ext: External Adversary&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Unauthenticated entity&lt;br/&gt;&amp;bull; Plain MQTT sniffing &amp;amp; spoofing&lt;/font&gt;" vertex="1">
          <mxGeometry x="250" y="90" width="230" height="100" as="geometry" />
        </mxCell>

        <!-- A_tenant -->
        <mxCell id="node_a_tenant" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 13px; color: #92400E;&quot;&gt;A_tenant: Cross-Tenant User&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Valid backend credentials&lt;br/&gt;&amp;bull; Horizontal privilege escalation&lt;/font&gt;" vertex="1">
          <mxGeometry x="510" y="90" width="230" height="100" as="geometry" />
        </mxCell>

        <!-- A_dos -->
        <mxCell id="node_a_dos" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#7C3AED;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 13px; color: #581C87;&quot;&gt;A_dos: Broker DoS &amp;amp; Freeze&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Event-loop thread freeze&lt;br/&gt;&amp;bull; Fake broker health status&lt;/font&gt;" vertex="1">
          <mxGeometry x="770" y="90" width="230" height="100" as="geometry" />
        </mxCell>

        <!-- A_edge -->
        <mxCell id="node_a_edge" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EFF6FF;strokeColor=#2563EB;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 13px; color: #1E40AF;&quot;&gt;A_edge: Compromised PT&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Valid hardware API key&lt;br/&gt;&amp;bull; Out-of-bounds &amp;amp; subtle drift&lt;/font&gt;" vertex="1">
          <mxGeometry x="1030" y="90" width="230" height="100" as="geometry" />
        </mxCell>

        <!-- ==================== MIDDLE ROW: 4 DEFENSE STAGES ==================== -->
        <!-- Stage 1 Container -->
        <mxCell id="stage1_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E3A8A;strokeWidth=2;verticalAlign=top;align=left;spacingLeft=14;spacingTop=45;" value="&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Hybrid TLS Handshake&lt;br/&gt;&amp;bull; REST Tokens &amp;amp; API Keys&lt;br/&gt;&amp;bull; In-Memory Vault Cache&lt;/font&gt;" vertex="1">
          <mxGeometry x="250" y="270" width="230" height="250" as="geometry" />
        </mxCell>
        <mxCell id="stage1_hdr" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1E3A8A;strokeColor=none;align=center;verticalAlign=middle;fontColor=#FFFFFF;fontSize=12;fontStyle=1;" value="Stage 1: Identity Auth" vertex="1">
          <mxGeometry x="250" y="270" width="230" height="40" as="geometry" />
        </mxCell>

        <!-- Stage 2 Container -->
        <mxCell id="stage2_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0F766E;strokeWidth=2;verticalAlign=top;align=left;spacingLeft=14;spacingTop=45;" value="&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Project ACL Isolation&lt;br/&gt;&amp;bull; Device Namespace Lock&lt;br/&gt;&amp;bull; Block Lateral Pivots&lt;/font&gt;" vertex="1">
          <mxGeometry x="510" y="270" width="230" height="250" as="geometry" />
        </mxCell>
        <mxCell id="stage2_hdr" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0F766E;strokeColor=none;align=center;verticalAlign=middle;fontColor=#FFFFFF;fontSize=12;fontStyle=1;" value="Stage 2: Scoped Topic ACL" vertex="1">
          <mxGeometry x="510" y="270" width="230" height="40" as="geometry" />
        </mxCell>

        <!-- Stage 3 Container -->
        <mxCell id="stage3_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#15803D;strokeWidth=2;verticalAlign=top;align=left;spacingLeft=14;spacingTop=45;" value="&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Signed Broker Heartbeat&lt;br/&gt;&amp;bull; dt/system/integrity topic&lt;br/&gt;&amp;bull; Thread Watchdog Monitor&lt;/font&gt;" vertex="1">
          <mxGeometry x="770" y="270" width="230" height="250" as="geometry" />
        </mxCell>
        <mxCell id="stage3_hdr" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#15803D;strokeColor=none;align=center;verticalAlign=middle;fontColor=#FFFFFF;fontSize=12;fontStyle=1;" value="Stage 3: Integrity Attest" vertex="1">
          <mxGeometry x="770" y="270" width="230" height="40" as="geometry" />
        </mxCell>

        <!-- Stage 4 Container -->
        <mxCell id="stage4_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4338CA;strokeWidth=2;verticalAlign=top;align=left;spacingLeft=14;spacingTop=45;" value="&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Layer A: DPI (&amp;le; 65 &amp;mu;s)&lt;br/&gt;&amp;bull; Layer B: VFAAD Fusion&lt;br/&gt;&amp;bull; Continuous Trust Index&lt;/font&gt;" vertex="1">
          <mxGeometry x="1030" y="270" width="230" height="250" as="geometry" />
        </mxCell>
        <mxCell id="stage4_hdr" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#4338CA;strokeColor=none;align=center;verticalAlign=middle;fontColor=#FFFFFF;fontSize=12;fontStyle=1;" value="Stage 4: Telemetry Guard" vertex="1">
          <mxGeometry x="1030" y="270" width="230" height="40" as="geometry" />
        </mxCell>

        <!-- DT Core -->
        <mxCell id="node_dt_core" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;strokeWidth=2.5;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 14px; color: #14532D;&quot;&gt;DIGITAL TWIN&lt;br/&gt;CORE&lt;/b&gt;&lt;br/&gt;&lt;br/&gt;&lt;font color=&#39;#15803D&#39; size=&#39;2&#39;&gt;&lt;b&gt;Zero-Trust State Sync&lt;/b&gt;&lt;br/&gt;TI &amp;ge; 0.70 Verified&lt;/font&gt;" vertex="1">
          <mxGeometry x="1290" y="270" width="110" height="250" as="geometry" />
        </mxCell>

        <!-- ==================== BOTTOM ROW: MITIGATION OUTCOMES ==================== -->
        <!-- Drop 1 -->
        <mxCell id="drop_1" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 12px; color: #991B1B;&quot;&gt;Drop Handshake&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;1&#39;&gt;Unauthenticated TCP Drop&lt;/font&gt;" vertex="1">
          <mxGeometry x="250" y="600" width="230" height="70" as="geometry" />
        </mxCell>

        <!-- Drop 2 -->
        <mxCell id="drop_2" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 12px; color: #92400E;&quot;&gt;Access Denied (0x87)&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;1&#39;&gt;MQTT Auth Disconnect&lt;/font&gt;" vertex="1">
          <mxGeometry x="510" y="600" width="230" height="70" as="geometry" />
        </mxCell>

        <!-- Drop 3 -->
        <mxCell id="drop_3" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#7C3AED;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 12px; color: #581C87;&quot;&gt;Detect DoS Freeze&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;1&#39;&gt;Heartbeat Timeout Alarm&lt;/font&gt;" vertex="1">
          <mxGeometry x="770" y="600" width="230" height="70" as="geometry" />
        </mxCell>

        <!-- Drop 4 -->
        <mxCell id="drop_4" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EFF6FF;strokeColor=#2563EB;strokeWidth=2;align=center;verticalAlign=middle;" value="&lt;b style=&quot;font-size: 12px; color: #1E40AF;&quot;&gt;Neutralize Edge Data&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;1&#39;&gt;DPI Fast Drop / Distrust&lt;/font&gt;" vertex="1">
          <mxGeometry x="1030" y="600" width="230" height="70" as="geometry" />
        </mxCell>

        <!-- ==================== CONNECTORS (ZERO OVERLAPPING) ==================== -->
        <!-- 1. Horizontal Green Pipeline Arrows -->
        <mxCell id="edge_legit_s1" edge="1" parent="1" source="node_legit" target="stage1_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#16A34A;strokeWidth=2.5;exitX=1;exitY=0.7;entryX=0;entryY=0.5;" value="Connect">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_s1_s2" edge="1" parent="1" source="stage1_box" target="stage2_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#16A34A;strokeWidth=2.5;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" value="Pass">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_s2_s3" edge="1" parent="1" source="stage2_box" target="stage3_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#16A34A;strokeWidth=2.5;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" value="Pass">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_s3_s4" edge="1" parent="1" source="stage3_box" target="stage4_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#16A34A;strokeWidth=2.5;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" value="Pass">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_s4_dt" edge="1" parent="1" source="stage4_box" target="node_dt_core" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#16A34A;strokeWidth=2.5;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" value="Sync">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- 2. Vertical Downward Attack Ingress Arrows -->
        <mxCell id="edge_att_s1" edge="1" parent="1" source="node_a_ext" target="stage1_hdr" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#DC2626;strokeWidth=2.2;strokeDashArray=3 3;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Attack">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_att_s2" edge="1" parent="1" source="node_a_tenant" target="stage2_hdr" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#D97706;strokeWidth=2.2;strokeDashArray=3 3;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Attack">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_att_s3" edge="1" parent="1" source="node_a_dos" target="stage3_hdr" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#7C3AED;strokeWidth=2.2;strokeDashArray=3 3;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Attack">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_att_s4" edge="1" parent="1" source="node_a_edge" target="stage4_hdr" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#2563EB;strokeWidth=2.2;strokeDashArray=3 3;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Attack">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- 3. Vertical Downward Mitigation Rejection Arrows -->
        <mxCell id="edge_drop_s1" edge="1" parent="1" source="stage1_box" target="drop_1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#DC2626;strokeWidth=2.2;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Violation">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_drop_s2" edge="1" parent="1" source="stage2_box" target="drop_2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#D97706;strokeWidth=2.2;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Violation">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_drop_s3" edge="1" parent="1" source="stage3_box" target="drop_3" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#7C3AED;strokeWidth=2.2;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Violation">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_drop_s4" edge="1" parent="1" source="stage4_box" target="drop_4" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#2563EB;strokeWidth=2.2;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="Violation">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    return xml


def create_hybrid_defense_drawio():
    xml = '''<mxfile host="app.diagrams.net" agent="Antigravity AI" version="24.7.5">
  <diagram id="dual-layer-telemetry-validation" name="Dual-Layer Telemetry Validation">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1420" pageHeight="820" background="#F8FAFC" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Canvas Header -->
        <mxCell id="canvas_title" parent="1" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=20;fontStyle=1;fontColor=#0F172A;" value="Dual-Layer Telemetry Validation Architecture (Hard vs. Soft Bounds)" vertex="1">
          <mxGeometry x="100" y="15" width="1220" height="35" as="geometry" />
        </mxCell>
        <mxCell id="canvas_subtitle" parent="1" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=13;fontStyle=2;fontColor=#334155;" value="Fast-Path DPI Model Reflection (Layer A) Coupled with Decoupled Value Fusion Anomaly Detection (Layer B)" vertex="1">
          <mxGeometry x="100" y="45" width="1220" height="25" as="geometry" />
        </mxCell>

        <!-- ==================== COLUMN CONTAINERS ==================== -->
        <!-- Col 1: Ingress & Model -->
        <mxCell id="col_ingress" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F1F5F9;strokeColor=#475569;strokeWidth=2;verticalAlign=top;align=center;spacingTop=12;fontColor=#1E293B;fontSize=14;fontStyle=1;" value="1. Telemetry Ingress &amp;amp; SSOT" vertex="1">
          <mxGeometry x="30" y="80" width="280" height="680" as="geometry" />
        </mxCell>

        <!-- Col 2: Layer A Fast Path -->
        <mxCell id="col_layer_a" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;verticalAlign=top;align=center;spacingTop=12;fontColor=#0369A1;fontSize=14;fontStyle=1;" value="2. Layer A: Inline Fast-Path DPI (&amp;le; 65 &amp;mu;s)" vertex="1">
          <mxGeometry x="340" y="80" width="340" height="680" as="geometry" />
        </mxCell>

        <!-- Col 3: Layer B Decoupled Anomaly Engine -->
        <mxCell id="col_layer_b" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#7C3AED;strokeWidth=2;verticalAlign=top;align=center;spacingTop=12;fontColor=#6D28D9;fontSize=14;fontStyle=1;" value="3. Layer B: Decoupled VFAAD Engine" vertex="1">
          <mxGeometry x="710" y="80" width="670" height="680" as="geometry" />
        </mxCell>

        <!-- ==================== COL 1 NODES ==================== -->
        <!-- Physical Twin Telemetry -->
        <mxCell id="node_pt_telemetry" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2563EB;strokeWidth=2;align=left;spacingLeft=14;" value="&lt;b style=&quot;font-size: 13px; color: #1E40AF;&quot;&gt;Physical Twin Stream&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Live JSON Sensor Packet&lt;br/&gt;&amp;bull; Speed, Temp, Battery SOC&lt;br/&gt;&amp;bull; Signed Hardware API Key&lt;/font&gt;" vertex="1">
          <mxGeometry x="50" y="130" width="240" height="110" as="geometry" />
        </mxCell>

        <!-- SysML v2 SSOT Model -->
        <mxCell id="node_sysml_ssot" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4338CA;strokeWidth=2;align=left;spacingLeft=14;" value="&lt;b style=&quot;font-size: 13px; color: #312E81;&quot;&gt;SysML v2 System Model (SSOT)&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Authoritative Constraints&lt;br/&gt;&amp;bull; Physical Operating Bounds&lt;br/&gt;&amp;bull; Dynamic Reflection API&lt;/font&gt;" vertex="1">
          <mxGeometry x="50" y="380" width="240" height="120" as="geometry" />
        </mxCell>

        <!-- ==================== COL 2: LAYER A NODES ==================== -->
        <!-- Layer A DPI Engine -->
        <mxCell id="node_layer_a_dpi" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0284C7;strokeWidth=2;align=left;spacingLeft=14;" value="&lt;b style=&quot;font-size: 13px; color: #0369A1;&quot;&gt;Inline Scalar DPI Engine&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Real-time payload check (&amp;le; 65 &amp;mu;s)&lt;br/&gt;&amp;bull; Evaluates: Vmin &amp;le; v &amp;le; Vmax&lt;br/&gt;&amp;bull; O(1) in-memory comparison&lt;/font&gt;" vertex="1">
          <mxGeometry x="365" y="130" width="290" height="110" as="geometry" />
        </mxCell>

        <!-- Layer A Decision -->
        <mxCell id="node_layer_a_check" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EFF6FF;strokeColor=#2563EB;strokeWidth=2;align=center;" value="&lt;b style=&quot;font-size: 13px; color: #1E40AF;&quot;&gt;Physical Bounds Satisfied?&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;All values within model ranges&lt;/font&gt;" vertex="1">
          <mxGeometry x="365" y="340" width="290" height="70" as="geometry" />
        </mxCell>

        <!-- Layer A Drop Node -->
        <mxCell id="node_layer_a_drop" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=2;align=center;" value="&lt;b style=&quot;font-size: 13px; color: #991B1B;&quot;&gt;HARD BOUNDS VIOLATION&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#B91C1C&#39; size=&#39;2&#39;&gt;&lt;b&gt;Drop Payload &amp;amp; Disconnect (0x87)&lt;/b&gt;&lt;/font&gt;" vertex="1">
          <mxGeometry x="365" y="520" width="290" height="75" as="geometry" />
        </mxCell>

        <!-- ==================== COL 3: LAYER B NODES ==================== -->
        <!-- Estimators -->
        <mxCell id="node_z_score" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=2;align=left;spacingLeft=14;" value="&lt;b style=&quot;font-size: 13px; color: #581C87;&quot;&gt;Univariate Z-Score&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; Running Variance Tracking&lt;br/&gt;&amp;bull; Rapid Thermal Surges&lt;/font&gt;" vertex="1">
          <mxGeometry x="740" y="130" width="290" height="95" as="geometry" />
        </mxCell>

        <mxCell id="node_if_forest" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=2;align=left;spacingLeft=14;" value="&lt;b style=&quot;font-size: 13px; color: #581C87;&quot;&gt;Multivariate Isolation Forest&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;&amp;bull; 100-Tree High-Dim Ensemble&lt;br/&gt;&amp;bull; Multi-Sensor Drift Detection&lt;/font&gt;" vertex="1">
          <mxGeometry x="1060" y="130" width="290" height="95" as="geometry" />
        </mxCell>

        <!-- Mamdani Value Fusion -->
        <mxCell id="node_mamdani" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F3E8FF;strokeColor=#6D28D9;strokeWidth=2;align=center;" value="&lt;b style=&quot;font-size: 14px; color: #4C1D95;&quot;&gt;Mamdani Fuzzy Value Fusion Engine&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#0F172A&#39; size=&#39;2&#39;&gt;Fuses Z-Score + IF-Score metrics via 9 expert inference rules&lt;br/&gt;Centroid Defuzzification &amp;rarr; &lt;b&gt;Continuous Trust Index (TI &amp;isin; [0, 1])&lt;/b&gt;&lt;/font&gt;" vertex="1">
          <mxGeometry x="740" y="325" width="610" height="90" as="geometry" />
        </mxCell>

        <!-- Decision Tiers -->
        <mxCell id="node_tier1" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;strokeWidth=2;align=center;" value="&lt;b style=&quot;font-size: 13px; color: #14532D;&quot;&gt;TI &amp;ge; 0.70&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#15803D&#39; size=&#39;2&#39;&gt;&lt;b&gt;NOMINAL&lt;/b&gt;&lt;br/&gt;Full Twin Sync&lt;/font&gt;" vertex="1">
          <mxGeometry x="740" y="515" width="185" height="85" as="geometry" />
        </mxCell>

        <mxCell id="node_tier2" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=2;align=center;" value="&lt;b style=&quot;font-size: 13px; color: #78350F;&quot;&gt;0.30 &amp;le; TI &amp;lt; 0.70&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#92400E&#39; size=&#39;2&#39;&gt;&lt;b&gt;WARNING&lt;/b&gt;&lt;br/&gt;Sensor Alert&lt;/font&gt;" vertex="1">
          <mxGeometry x="952" y="515" width="185" height="85" as="geometry" />
        </mxCell>

        <mxCell id="node_tier3" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=2;align=center;" value="&lt;b style=&quot;font-size: 13px; color: #7F1D1D;&quot;&gt;TI &amp;lt; 0.30&lt;/b&gt;&lt;br/&gt;&lt;font color=&#39;#991B1B&#39; size=&#39;2&#39;&gt;&lt;b&gt;CRITICAL&lt;/b&gt;&lt;br/&gt;Reject Sync&lt;/font&gt;" vertex="1">
          <mxGeometry x="1165" y="515" width="185" height="85" as="geometry" />
        </mxCell>

        <!-- ==================== CONNECTORS (ZERO OVERLAPPING) ==================== -->
        <!-- Ingress Telemetry: PT Stream -> Layer A DPI -->
        <mxCell id="edge_pt_dpi" edge="1" parent="1" source="node_pt_telemetry" target="node_layer_a_dpi" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#2563EB;strokeWidth=2.5;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" value="Telemetry">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- SysML SSOT to Layer A DPI -->
        <mxCell id="edge_ssot_dpi" edge="1" parent="1" source="node_sysml_ssot" target="node_layer_a_dpi" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#4338CA;strokeWidth=2.2;strokeDashArray=3 3;exitX=1;exitY=0.5;entryX=0;entryY=0.8;" value="Model Bounds">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Layer A DPI to Decision (Straight Down) -->
        <mxCell id="edge_dpi_check" edge="1" parent="1" source="node_layer_a_dpi" target="node_layer_a_check" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0284C7;strokeWidth=2.2;exitX=0.5;exitY=1;entryX=0.5;entryY=0;">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Decision [NO] to Drop (Straight Down) -->
        <mxCell id="edge_check_no" edge="1" parent="1" source="node_layer_a_check" target="node_layer_a_drop" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#DC2626;strokeWidth=2.2;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" value="[NO] Limit Exceeded">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Decision [YES] to Layer B Estimators (Async Hand-off) -->
        <mxCell id="edge_check_yes_z" edge="1" parent="1" source="node_layer_a_check" target="node_z_score" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#16A34A;strokeWidth=2.5;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" value="In-Bounds Async Queue">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Estimators to Mamdani (Straight Down) -->
        <mxCell id="edge_z_mamdani" edge="1" parent="1" source="node_z_score" target="node_mamdani" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#6D28D9;strokeWidth=2.0;exitX=0.5;exitY=1;entryX=0.25;entryY=0;">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_if_mamdani" edge="1" parent="1" source="node_if_forest" target="node_mamdani" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#6D28D9;strokeWidth=2.0;exitX=0.5;exitY=1;entryX=0.75;entryY=0;">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Mamdani to Tiers (Straight Down) -->
        <mxCell id="edge_m_t1" edge="1" parent="1" source="node_mamdani" target="node_tier1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#16A34A;strokeWidth=2.0;exitX=0.15;exitY=1;entryX=0.5;entryY=0;">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_m_t2" edge="1" parent="1" source="node_mamdani" target="node_tier2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#D97706;strokeWidth=2.0;exitX=0.5;exitY=1;entryX=0.5;entryY=0;">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge_m_t3" edge="1" parent="1" source="node_mamdani" target="node_tier3" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#DC2626;strokeWidth=2.0;exitX=0.85;exitY=1;entryX=0.5;entryY=0;">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    return xml


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, "../.."))
    figures_dir = os.path.join(base_dir, "latex-master-BachelorMasterThesis/BachelorMasterThesis/figures")

    threat_xml = create_threat_mitigation_drawio()
    hybrid_xml = create_hybrid_defense_drawio()

    paths = [
        (os.path.join(script_dir, "threat_mitigation_pipeline.drawio"), threat_xml),
        (os.path.join(figures_dir, "threat_mitigation_pipeline.drawio"), threat_xml),
        (os.path.join(script_dir, "hybrid_defense_concept.drawio"), hybrid_xml),
        (os.path.join(figures_dir, "hybrid_defense_concept.drawio"), hybrid_xml),
    ]

    for p, content in paths:
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated Draw.io diagram at: {p}")

if __name__ == "__main__":
    main()
