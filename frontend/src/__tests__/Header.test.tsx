import { render, screen } from "@testing-library/react";
import Header from "../components/Header";
import { UserProvider } from "../components/UserProvider";

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
  usePathname: () => "/",
}));

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ username: "testuser" }),
    }),
  ) as jest.Mock;
});

afterEach(() => {
  jest.restoreAllMocks();
});

it("renders the header and displays user information", async () => {
  render(
    <UserProvider>
      <Header
        onApplyFilters={jest.fn()}
        initialFilters={{
          speciesName: null,
          commonName: null,
          minDate: null,
          maxDate: null,
        }}
      />
    </UserProvider>,
  );

  expect(screen.getByText("Syncing System...")).toBeInTheDocument();

  expect(await screen.findByText("Operator: testuser")).toBeInTheDocument();
});
