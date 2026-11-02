using System.Net;
using System.Text.Json;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Mvc.Testing;

namespace HomebrewApp.Tests.Features.Health;

public class HealthEndpointsTests(WebApplicationFactory<Program> factory)
    : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task HealthEndpoint_ReturnsOkWithStatusOk()
    {
        var client = factory.CreateClient();

        var response = await client.GetAsync("/api/health");

        Assert.Equal(response.StatusCode, HttpStatusCode.OK);

        using var document = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync());
        var root = document.RootElement;

        // This throws an exception if 'status' (case-sensitive) doesn't exist
        var statusProperty = root.GetProperty("status");

        Assert.Equal("ok", statusProperty.GetString());
    }
}
