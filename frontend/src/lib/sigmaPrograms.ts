import type { NodeDisplayData, RenderParams } from "sigma/types";

const BORDERED_NODE_VERT = `
attribute vec2 a_position;
attribute float a_size;
attribute vec4 a_color;
attribute vec4 a_borderColor;
attribute float a_borderWidth;
attribute float a_glow;

uniform mat3 u_matrix;
uniform float u_ratio;
uniform float u_pixelRatio;

varying vec4 v_color;
varying vec4 v_borderColor;
varying float v_borderWidth;
varying float v_glow;
varying float v_pointSize;

void main() {
  vec2 pos = (u_matrix * vec3(a_position, 1)).xy;
  gl_Position = vec4(pos, 0, 1);
  gl_PointSize = a_size * 2.0 * u_pixelRatio / u_ratio;
  v_color = a_color;
  v_borderColor = a_borderColor;
  v_borderWidth = a_borderWidth;
  v_glow = a_glow;
  v_pointSize = gl_PointSize;
}
`;

const BORDERED_NODE_FRAG = `
precision mediump float;

varying vec4 v_color;
varying vec4 v_borderColor;
varying float v_borderWidth;
varying float v_glow;
varying float v_pointSize;

void main() {
  vec2 c = gl_PointCoord.xy - vec2(0.5);
  float r = length(c) * 2.0;

  float edge = 1.5 / max(v_pointSize, 40.0);
  float alpha = 1.0 - smoothstep(1.0 - edge, 1.0 + edge, r);
  if (alpha <= 0.0) discard;

  float bw = clamp(v_borderWidth, 0.0, 6.0);
  float borderT = bw / max(v_pointSize, 1.0) * 2.0;
  float borderMix = smoothstep(1.0 - borderT - edge, 1.0 - borderT + edge, r);

  vec4 base = mix(v_borderColor, v_color, borderMix);

  float glow = clamp(v_glow, 0.0, 1.0);
  float glowAlpha = (1.0 - smoothstep(0.65, 1.0, r)) * 0.22 * glow;
  vec4 glowColor = vec4(v_borderColor.rgb, glowAlpha);

  #if PICKING_MODE
  gl_FragColor = vec4(v_color.rgb, 1.0);
  #else
  gl_FragColor = vec4(base.rgb, base.a * alpha) + glowColor;
  #endif
}
`;

export async function loadBorderedNodeProgram() {
  const mod = await import("sigma/rendering");
  const ProgramBase = (mod as any).Program;

  return class BorderedNodeProgram extends ProgramBase {
    constructor(...args: any[]) {
      super(...args);
      if (!(this as any).gl && args.length) (this as any).gl = args[0];
    }

    static getDefinition() {
      return {
        VERTICES: 1,
        VERTEX_SHADER_SOURCE: BORDERED_NODE_VERT,
        FRAGMENT_SHADER_SOURCE: BORDERED_NODE_FRAG,
        METHOD: WebGLRenderingContext.POINTS,
        ATTRIBUTES: [
          { name: "a_position", size: 2, type: WebGLRenderingContext.FLOAT },
          { name: "a_size", size: 1, type: WebGLRenderingContext.FLOAT },
          { name: "a_color", size: 4, type: WebGLRenderingContext.UNSIGNED_BYTE, normalized: true },
          { name: "a_borderColor", size: 4, type: WebGLRenderingContext.UNSIGNED_BYTE, normalized: true },
          { name: "a_borderWidth", size: 1, type: WebGLRenderingContext.FLOAT },
          { name: "a_glow", size: 1, type: WebGLRenderingContext.FLOAT },
        ],
        UNIFORMS: [
          { name: "u_matrix", size: 9, type: WebGLRenderingContext.FLOAT },
          { name: "u_ratio", size: 1, type: WebGLRenderingContext.FLOAT },
          { name: "u_pixelRatio", size: 1, type: WebGLRenderingContext.FLOAT },
        ],
      };
    }

    getDefinition() {
      return (this.constructor as any).getDefinition();
    }

    processVisibleItem(offset: number, data: NodeDisplayData) {
      const a = this.array;

      const x = data.x;
      const y = data.y;
      const size = data.size || 4;

      const fill = (data as any).fillColor || (data as any).color;
      const border = (data as any).borderColor || (data as any).color;

      void fill;
      void border;

      const fillRGBA: number[] = (data as any).fillColorRGBA || [156, 163, 175, 255];
      const borderRGBA: number[] = (data as any).borderColorRGBA || fillRGBA;

      const borderWidth = (data as any).borderWidth ?? 1.5;
      const glow = (data as any).glow ?? 0.0;

      let i = offset;
      a[i++] = x;
      a[i++] = y;
      a[i++] = size;

      a[i++] = fillRGBA[0];
      a[i++] = fillRGBA[1];
      a[i++] = fillRGBA[2];
      a[i++] = fillRGBA[3];

      a[i++] = borderRGBA[0];
      a[i++] = borderRGBA[1];
      a[i++] = borderRGBA[2];
      a[i++] = borderRGBA[3];

      a[i++] = borderWidth;
      a[i++] = glow;
    }

    process(offset: number, data: NodeDisplayData) {
      this.processVisibleItem(offset, data);
    }

    setUniforms(params: RenderParams) {
      const gl = ((params as any).gl || (this as any).gl) as WebGLRenderingContext | undefined;
      if (!gl) return;
      const uniforms = ((this as any).uniformLocations || (params as any).uniformLocations || {}) as any;
      const matrix = (params as any).matrix;
      if (!uniforms.u_matrix || !matrix) return;
      gl.uniformMatrix3fv(uniforms.u_matrix, false, matrix);
      if (uniforms.u_ratio) gl.uniform1f(uniforms.u_ratio, (params as any).ratio ?? 1);
      if (uniforms.u_pixelRatio) gl.uniform1f(uniforms.u_pixelRatio, (params as any).pixelRatio ?? 1);
    }

    draw(params: RenderParams) {
      const gl = ((params as any).gl || (this as any).gl) as WebGLRenderingContext | undefined;
      if (!gl) return;
      const program = ((this as any).program || (params as any).program) as WebGLProgram | undefined;
      if (program) gl.useProgram(program);
      this.setUniforms(params);
      gl.drawArrays(gl.POINTS, 0, (this as any).verticesCount || 0);
    }
  };
}

export async function loadDashedEdgeProgram() {
  const mod = await import("sigma/rendering");
  const ProgramBase = (mod as any).Program;

  const vert = `
attribute vec2 a_position;
attribute float a_u;
attribute vec4 a_color;

uniform mat3 u_matrix;
uniform float u_ratio;

varying float v_u;
varying vec4 v_color;

void main() {
  vec2 pos = (u_matrix * vec3(a_position, 1)).xy;
  gl_Position = vec4(pos, 0, 1);
  v_u = a_u;
  v_color = a_color;
}
`;

  const frag = `
precision mediump float;

varying float v_u;
varying vec4 v_color;

uniform float u_dashCount;
uniform float u_dashFill;

void main() {
  float t = fract(v_u * u_dashCount);
  float on = step(t, u_dashFill);
  if (on < 0.5) discard;
  gl_FragColor = v_color;
}
`;

  return class DashedEdgeProgram extends ProgramBase {
    constructor(...args: any[]) {
      super(...args);
      if (!(this as any).gl && args.length) (this as any).gl = args[0];
    }

    static getDefinition() {
      return {
        VERTICES: 6,
        VERTEX_SHADER_SOURCE: vert,
        FRAGMENT_SHADER_SOURCE: frag,
        METHOD: WebGLRenderingContext.TRIANGLES,
        ATTRIBUTES: [
          { name: "a_position", size: 2, type: WebGLRenderingContext.FLOAT },
          { name: "a_u", size: 1, type: WebGLRenderingContext.FLOAT },
          { name: "a_color", size: 4, type: WebGLRenderingContext.UNSIGNED_BYTE, normalized: true },
        ],
        UNIFORMS: [
          { name: "u_matrix", size: 9, type: WebGLRenderingContext.FLOAT },
          { name: "u_ratio", size: 1, type: WebGLRenderingContext.FLOAT },
          { name: "u_dashCount", size: 1, type: WebGLRenderingContext.FLOAT },
          { name: "u_dashFill", size: 1, type: WebGLRenderingContext.FLOAT },
        ],
      };
    }

    getDefinition() {
      return (this.constructor as any).getDefinition();
    }

    processVisibleItem(offset: number, data: any) {
      const a = this.array;

      const sx = data.sourceX ?? data.source?.x ?? 0;
      const sy = data.sourceY ?? data.source?.y ?? 0;
      const tx = data.targetX ?? data.target?.x ?? 0;
      const ty = data.targetY ?? data.target?.y ?? 0;

      const thickness = Number(data.thickness ?? data.size ?? 1.0);
      const rgba: number[] = data.colorRGBA || [234, 88, 12, 160];

      const dx = tx - sx;
      const dy = ty - sy;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      const ux = dx / len;
      const uy = dy / len;
      const nx = -uy;
      const ny = ux;
      const half = Math.max(0.0001, thickness / 2);

      const x1 = sx + nx * half;
      const y1 = sy + ny * half;
      const x2 = sx - nx * half;
      const y2 = sy - ny * half;
      const x3 = tx + nx * half;
      const y3 = ty + ny * half;
      const x4 = tx - nx * half;
      const y4 = ty - ny * half;

      let i = offset;

      a[i++] = x1;
      a[i++] = y1;
      a[i++] = 0;
      a[i++] = rgba[0];
      a[i++] = rgba[1];
      a[i++] = rgba[2];
      a[i++] = rgba[3];

      a[i++] = x2;
      a[i++] = y2;
      a[i++] = 0;
      a[i++] = rgba[0];
      a[i++] = rgba[1];
      a[i++] = rgba[2];
      a[i++] = rgba[3];

      a[i++] = x3;
      a[i++] = y3;
      a[i++] = 1;
      a[i++] = rgba[0];
      a[i++] = rgba[1];
      a[i++] = rgba[2];
      a[i++] = rgba[3];

      a[i++] = x3;
      a[i++] = y3;
      a[i++] = 1;
      a[i++] = rgba[0];
      a[i++] = rgba[1];
      a[i++] = rgba[2];
      a[i++] = rgba[3];

      a[i++] = x2;
      a[i++] = y2;
      a[i++] = 0;
      a[i++] = rgba[0];
      a[i++] = rgba[1];
      a[i++] = rgba[2];
      a[i++] = rgba[3];

      a[i++] = x4;
      a[i++] = y4;
      a[i++] = 1;
      a[i++] = rgba[0];
      a[i++] = rgba[1];
      a[i++] = rgba[2];
      a[i++] = rgba[3];
    }

    process(offset: number, data: any) {
      this.processVisibleItem(offset, data);
    }

    setUniforms(params: RenderParams) {
      const gl = ((params as any).gl || (this as any).gl) as WebGLRenderingContext | undefined;
      if (!gl) return;
      const uniforms = ((this as any).uniformLocations || (params as any).uniformLocations || {}) as any;
      const matrix = (params as any).matrix;
      if (uniforms.u_matrix && matrix) gl.uniformMatrix3fv(uniforms.u_matrix, false, matrix);
      const ratio = (params as any).ratio ?? 1;
      if (uniforms.u_ratio) gl.uniform1f(uniforms.u_ratio, ratio);
      if (uniforms.u_dashCount) gl.uniform1f(uniforms.u_dashCount, Math.max(6, Math.min(18, 12 / Math.max(0.6, Math.min(1.8, ratio)))));
      if (uniforms.u_dashFill) gl.uniform1f(uniforms.u_dashFill, 0.55);
    }

    draw(params: RenderParams) {
      const gl = ((params as any).gl || (this as any).gl) as WebGLRenderingContext | undefined;
      if (!gl) return;
      const program = ((this as any).program || (params as any).program) as WebGLProgram | undefined;
      if (program) gl.useProgram(program);
      this.setUniforms(params);
      gl.drawArrays(gl.TRIANGLES, 0, (this as any).verticesCount || 0);
    }
  };
}

export function hexToRgbaBytes(hex: string, alpha = 1): [number, number, number, number] {
  const h = hex.replace("#", "").trim();
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const a = Math.max(0, Math.min(255, Math.round(alpha * 255)));
  return [r, g, b, a];
}
