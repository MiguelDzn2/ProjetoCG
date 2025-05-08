out vec4 fragColor;
in vec2 v_texCoords;

uniform sampler2D ssaoInput; // Raw SSAO texture

void main()
{
    vec2 texelSize = 1.0 / textureSize(ssaoInput, 0); // Get dimensions of level 0
    float result = 0.0;

    // 3x3 Box Blur
    for (int x = -1; x <= 1; ++x)
    {
        for (int y = -1; y <= 1; ++y)
        {
            vec2 offset = vec2(float(x), float(y)) * texelSize;
            result += texture(ssaoInput, v_texCoords + offset).r; // Changed from TexCoords. SSAO is in the red channel
        }
    }
    result /= 9.0;

    fragColor = vec4(result, result, result, 1.0); // Output blurred SSAO
} 