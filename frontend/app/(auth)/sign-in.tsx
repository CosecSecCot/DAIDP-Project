import { AuthView } from "@clerk/expo/native";
import { useAuth } from "@clerk/expo";
import { useRouter } from "expo-router";
import { useEffect } from "react";

export default function SignInScreen() {
  const { isSignedIn, isLoaded } = useAuth({ treatPendingAsSignedOut: false });
  const router = useRouter();

  useEffect(() => {
    console.log("isLoaded", isLoaded);

    if (!isLoaded) {
      return;
    }

    console.log("isSignedIn", isSignedIn);

    if (isSignedIn) {
      router.replace("/");
    }
  }, [isSignedIn, isLoaded, router]);

  return <AuthView mode="signInOrUp" />;
}
