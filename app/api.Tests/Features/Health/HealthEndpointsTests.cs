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

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        using var document = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync());
        var root = document.RootElement;

        // This throws an exception if 'status' (case-sensitive) doesn't exist
        var statusProperty = root.GetProperty("status");

        Assert.Equal("ok", statusProperty.GetString());
    }

    [Fact]
    public async Task HealthEndpoint_DatabaseUnreachable_ReturnsOkWithDatabaseDown()
    {
        var client = factory
            .WithWebHostBuilder(builder => builder.UseSetting("ConnectionStrings:App",
                "Host=127.0.0.1;Port=1;Database=postgres;Username=test;Password=test"))
            .CreateClient();

        var response = await client.GetAsync("/api/health");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        using var document = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync());
        var root = document.RootElement;

        var statusProperty = root.GetProperty("status");
        var databaseProperty = root.GetProperty("database");

        Assert.Equal("ok", statusProperty.GetString());
        Assert.Equal("down", databaseProperty.GetString());
    }
}
